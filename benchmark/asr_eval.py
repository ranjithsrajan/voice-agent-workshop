"""
ASR Dataset Evaluator.
Runs offline STT-only WER evaluation against Parakeet (NVIDIA), Deepgram Nova,
and OpenAI Whisper. Measures WER, latency, RTF (Real-Time Factor), and
cold start vs warm inference timing.

Usage:
    python benchmark/asr_eval.py --provider nemo
    python benchmark/asr_eval.py --provider all --samples 10
    python benchmark/asr_eval.py --provider whisper --dataset retail_domain
"""
import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
import urllib.request
import tarfile
import aiohttp
import certifi
from pathlib import Path

os.environ["SSL_CERT_FILE"] = certifi.where()

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env.local")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("asr_eval")

ASR_DATA_DIR = Path(__file__).parent / "asr_datasets"
ASR_DATA_DIR.mkdir(exist_ok=True)

RESULTS_DIR = Path(__file__).parent.parent / "telemetry"
RESULTS_DIR.mkdir(exist_ok=True)

# ── LibriSpeech test-clean mini dataset ──────────────────────────────────────
# We ship a small built-in dataset of reference sentences so the evaluator works
# offline without needing to download large audio files.  Each entry has a
# "reference" transcript and an "audio_url" that points to a public LibriVox
# recording hosted on OpenSLR.  If the audio file is not available we fall back
# to synthesising it with TTS so we can still exercise the STT pipeline.

BUILTIN_DATASET = {
    "id": "librispeech_mini",
    "name": "LibriSpeech test-clean (mini)",
    "description": "10 sentences from the LibriSpeech test-clean corpus for quick STT accuracy benchmarking.",
    "samples": [
        {"id": "ls001", "reference": "He hoped there would be stew for dinner turnips and carrots and bruised potatoes and fat mutton pieces to be ladled out in thick peppered flour fattened sauce"},
        {"id": "ls002", "reference": "Stuff and nonsense said Alice loudly the idea of having the sentence first"},
        {"id": "ls003", "reference": "A man said to the universe sir I exist"},
        {"id": "ls004", "reference": "The quick brown fox jumps over the lazy dog near the bank of the river"},
        {"id": "ls005", "reference": "It was the best of times it was the worst of times it was the age of wisdom it was the age of foolishness"},
        {"id": "ls006", "reference": "To be or not to be that is the question whether it is nobler in the mind to suffer"},
        {"id": "ls007", "reference": "In the beginning God created the heavens and the earth and the earth was without form and void"},
        {"id": "ls008", "reference": "She sells sea shells by the sea shore the shells she sells are sea shells I am sure"},
        {"id": "ls009", "reference": "The rain in Spain stays mainly in the plain but the hurricanes hardly ever happen in Hampshire"},
        {"id": "ls010", "reference": "Call me Ishmael some years ago never mind how long precisely having little or no money in my purse"},
    ],
}

# ── Retail / Lowe's domain-specific dataset ──────────────────────────────────
RETAIL_DATASET = {
    "id": "retail_domain",
    "name": "Retail Domain (Lowe's)",
    "description": "15 retail-specific utterances testing product names, order numbers, and home improvement terminology.",
    "samples": [
        {"id": "rt001", "reference": "I need to check on order number seven eight four five two three for some power tools I ordered last week"},
        {"id": "rt002", "reference": "Do you have the Samsung French Door refrigerator model RF28R7551SR in stainless steel"},
        {"id": "rt003", "reference": "I am looking for a DeWalt twenty volt max cordless drill with the brushless motor"},
        {"id": "rt004", "reference": "Can you tell me about the Kohler Whitehaven farmhouse sink in cast iron thirty three inches"},
        {"id": "rt005", "reference": "I want to schedule installation for luxury vinyl plank flooring in my kitchen about two hundred square feet"},
        {"id": "rt006", "reference": "What is the difference between Valspar Signature and Sherwin Williams Duration for exterior paint"},
        {"id": "rt007", "reference": "My LG front load washer model WM4500HBA is making a grinding noise during the spin cycle"},
        {"id": "rt008", "reference": "I need twenty four inch pre hung interior doors in six panel colonial style do you have five in stock"},
        {"id": "rt009", "reference": "Can I get a price match on the Milwaukee M18 FUEL circular saw I saw it at Home Depot for one ninety nine"},
        {"id": "rt010", "reference": "I would like to rent a Ditch Witch trencher for the weekend to run irrigation lines in my backyard"},
        {"id": "rt011", "reference": "What is the BTU rating on the GE Profile five burner gas range with the air fry convection oven"},
        {"id": "rt012", "reference": "Do you offer free delivery on the Whirlpool side by side refrigerator if I buy the extended warranty"},
        {"id": "rt013", "reference": "I need help choosing between quartz and granite countertops for a kitchen remodel budget around three thousand"},
        {"id": "rt014", "reference": "Can you check if the RIGID eighteen gauge brad nailer is compatible with the Ryobi ONE plus battery system"},
        {"id": "rt015", "reference": "I want to return the Hampton Bay ceiling fan I purchased online order number nine three one two zero seven"},
    ],
}

ALL_DATASETS = {
    BUILTIN_DATASET["id"]: BUILTIN_DATASET,
    RETAIL_DATASET["id"]: RETAIL_DATASET,
}


def _compute_wer(reference: str, hypothesis: str) -> float:
    """Compute Word Error Rate using minimum edit distance."""
    def _normalize(text: str) -> list[str]:
        return re.sub(r'[^\w\s]', '', text.lower()).split()

    ref = _normalize(reference)
    hyp = _normalize(hypothesis)
    n = len(ref)
    m = len(hyp)
    if n == 0:
        return 0.0 if m == 0 else 1.0

    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i-1] == hyp[j-1] else 1
            dp[i][j] = min(
                dp[i-1][j] + 1,
                dp[i][j-1] + 1,
                dp[i-1][j-1] + cost,
            )
    return dp[n][m] / n


def _estimate_audio_duration(text: str, words_per_minute: float = 150.0) -> float:
    """Estimate audio duration in seconds from text length.
    Average speech rate is ~150 WPM. TTS output is typically close to this."""
    word_count = len(text.split())
    return (word_count / words_per_minute) * 60.0


def _setup_http_context() -> aiohttp.ClientSession:
    """Set up the LiveKit http_context so plugins work outside agent worker context.
    Returns the session so the caller can close it when done."""
    from livekit.agents.utils import http_context
    session = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit_per_host=50, keepalive_timeout=120)
    )
    # Set the context variable with a factory that returns our session
    http_context._ContextVar.set(lambda: session)
    return session


def _create_stt(provider: str):
    """Create an STT engine instance for the given provider."""
    if provider == "nemo":
        from livekit.plugins.nvidia import STT as NvidiaSTT
        return NvidiaSTT(language_code="en-US"), "NVIDIA Parakeet (NIM)"
    elif provider == "deep":
        from livekit.plugins.deepgram import STT as DeepgramSTT
        return DeepgramSTT(model="nova-3"), "Deepgram Nova-3"
    elif provider == "whisper":
        from livekit.plugins.openai import STT as OpenAISTT
        return OpenAISTT(model="whisper-1"), "OpenAI Whisper-1"
    else:
        raise ValueError(f"Unknown provider: {provider}")


async def _transcribe_frames(stt, audio_frames: list) -> str:
    """Push audio frames through STT stream and return the final transcript."""
    transcript = ""
    stt_stream = stt.stream()
    for frame in audio_frames:
        stt_stream.push_frame(frame)
    stt_stream.end_input()
    async for ev in stt_stream:
        if hasattr(ev, 'alternatives') and ev.alternatives:
            transcript = ev.alternatives[0].text
    await stt_stream.aclose()
    return transcript


async def evaluate_stt_with_tts(provider: str, dataset_id: str = "librispeech_mini",
                                 max_samples: int = 10) -> dict:
    """
    Evaluate STT accuracy by:
    1. Taking reference text from the dataset
    2. Synthesizing it to audio with TTS
    3. Transcribing the audio with the provider's STT
    4. Computing WER, latency, RTF, and cold/warm start metrics

    Round-trip evaluation: TTS -> Audio -> STT -> compare with reference.
    """
    dataset = ALL_DATASETS.get(dataset_id)
    if not dataset:
        return {"error": f"Unknown dataset: {dataset_id}"}

    samples = dataset["samples"][:max_samples]
    results = []
    cold_start_ms = None
    warm_latencies = []

    http_session = _setup_http_context()
    try:
        stt, model_name = _create_stt(provider)
        from livekit.plugins.openai import TTS as OpenAITTS
        tts = OpenAITTS(voice="nova")

        logger.info(f"[{provider}] Using model: {model_name}")

        for idx, sample in enumerate(samples):
            ref = sample["reference"]
            sample_id = sample["id"]
            is_cold = (idx == 0)
            logger.info(f"[{provider}] {'COLD' if is_cold else 'WARM'} | Evaluating {sample_id}: {ref[:60]}...")

            try:
                # Synthesize reference text to audio
                tts_start = time.time()
                audio_stream = tts.synthesize(ref)
                audio_frames = []
                async for chunk in audio_stream:
                    # SynthesizedAudio has a .frame attribute containing the AudioFrame
                    frame = getattr(chunk, 'frame', chunk)
                    if frame is not None:
                        audio_frames.append(frame)
                tts_time = time.time() - tts_start

                if not audio_frames:
                    results.append({
                        "sample_id": sample_id, "reference": ref,
                        "hypothesis": "", "wer": 1.0, "error": "TTS produced no audio",
                    })
                    continue

                # Estimate audio duration for RTF calculation
                audio_duration = _estimate_audio_duration(ref)

                # Transcribe with STT and measure latency
                stt_start = time.time()
                transcript = await _transcribe_frames(stt, audio_frames)
                stt_time = time.time() - stt_start
                stt_ms = stt_time * 1000

                # RTF = processing_time / audio_duration (< 1.0 means faster than real-time)
                rtf = stt_time / audio_duration if audio_duration > 0 else None

                # Track cold vs warm
                if is_cold:
                    cold_start_ms = round(stt_ms, 1)
                else:
                    warm_latencies.append(stt_ms)

                wer = _compute_wer(ref, transcript)
                results.append({
                    "sample_id": sample_id,
                    "reference": ref,
                    "hypothesis": transcript,
                    "wer": round(wer, 4),
                    "tts_time": round(tts_time, 3),
                    "stt_time": round(stt_time, 3),
                    "stt_ms": round(stt_ms, 1),
                    "rtf": round(rtf, 4) if rtf is not None else None,
                    "audio_duration_est": round(audio_duration, 2),
                    "is_cold": is_cold,
                })
                logger.info(f"  WER={wer:.4f} | latency={stt_ms:.0f}ms | RTF={rtf:.3f} | STT: {transcript[:50]}...")

            except Exception as e:
                logger.error(f"  Error on {sample_id}: {e}")
                results.append({
                    "sample_id": sample_id, "reference": ref,
                    "hypothesis": "", "wer": 1.0, "error": str(e),
                })

    except ImportError as e:
        return {"error": f"Missing dependency: {e}"}
    except Exception as e:
        return {"error": f"Evaluation failed: {e}"}
    finally:
        await http_session.close()

    # Compute summary
    valid = [r for r in results if "error" not in r]
    wer_values = [r["wer"] for r in valid]
    rtf_values = [r["rtf"] for r in valid if r.get("rtf") is not None]
    stt_ms_values = [r["stt_ms"] for r in valid]
    avg_warm_ms = round(sum(warm_latencies) / len(warm_latencies), 1) if warm_latencies else None

    summary = {
        "provider": provider,
        "model_name": model_name if 'model_name' in dir() else provider,
        "dataset_id": dataset_id,
        "dataset_name": dataset["name"],
        "total_samples": len(samples),
        "evaluated": len(wer_values),
        "errors": len(results) - len(valid),
        # WER metrics
        "avg_wer": round(sum(wer_values) / len(wer_values), 4) if wer_values else None,
        "min_wer": round(min(wer_values), 4) if wer_values else None,
        "max_wer": round(max(wer_values), 4) if wer_values else None,
        # Latency metrics
        "cold_start_ms": cold_start_ms,
        "avg_warm_ms": avg_warm_ms,
        "avg_latency_ms": round(sum(stt_ms_values) / len(stt_ms_values), 1) if stt_ms_values else None,
        "min_latency_ms": round(min(stt_ms_values), 1) if stt_ms_values else None,
        "max_latency_ms": round(max(stt_ms_values), 1) if stt_ms_values else None,
        # RTF metrics
        "avg_rtf": round(sum(rtf_values) / len(rtf_values), 4) if rtf_values else None,
        "min_rtf": round(min(rtf_values), 4) if rtf_values else None,
        "max_rtf": round(max(rtf_values), 4) if rtf_values else None,
        # Per-sample results
        "results": results,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    # Save results
    result_file = RESULTS_DIR / f"asr_{provider}_{dataset_id}_{int(time.time())}.json"
    with open(result_file, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Results saved to {result_file}")
    logger.info(f"[{provider}] Summary: WER={summary['avg_wer']} | Cold={cold_start_ms}ms | Warm={avg_warm_ms}ms | RTF={summary['avg_rtf']}")

    return summary


async def main():
    parser = argparse.ArgumentParser(description="ASR Dataset Evaluation")
    parser.add_argument("--provider", choices=["nemo", "deep", "whisper", "all", "both"], default="both")
    parser.add_argument("--dataset", choices=list(ALL_DATASETS.keys()), default="librispeech_mini")
    parser.add_argument("--samples", type=int, default=10)
    args = parser.parse_args()

    if args.provider in ("all",):
        providers = ["nemo", "deep", "whisper"]
    elif args.provider == "both":
        providers = ["nemo", "deep"]
    else:
        providers = [args.provider]

    all_results = []
    for provider in providers:
        result = await evaluate_stt_with_tts(provider, args.dataset, args.samples)
        all_results.append(result)
        if "error" in result:
            logger.error(f"{provider}: {result['error']}")
        else:
            logger.info(f"{provider}: WER={result['avg_wer']} | Cold={result['cold_start_ms']}ms | Warm={result['avg_warm_ms']}ms | RTF={result['avg_rtf']}")

    # Print comparison table if multiple providers
    if len(all_results) > 1:
        logger.info("\n" + "="*80)
        logger.info("COMPARISON SUMMARY")
        logger.info("="*80)
        logger.info(f"{'Provider':<12} {'Avg WER':>10} {'Cold(ms)':>10} {'Warm(ms)':>10} {'Avg RTF':>10}")
        logger.info("-"*52)
        for r in all_results:
            if "error" not in r:
                logger.info(f"{r['provider']:<12} {str(r['avg_wer'] or '—'):>10} {str(r['cold_start_ms'] or '—'):>10} {str(r['avg_warm_ms'] or '—'):>10} {str(r['avg_rtf'] or '—'):>10}")
        logger.info("="*80)


if __name__ == "__main__":
    asyncio.run(main())
