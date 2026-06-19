"""
Benchmark server: launches agent runs and serves telemetry data for the dashboard.
"""
import os
import sys
import json
import glob
import signal
import subprocess
import time
import asyncio
import certifi
import threading
import re
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from typing import Optional


def _compute_wer(reference: str, hypothesis: str) -> float:
    """Compute Word Error Rate without external dependencies.
    WER = (S + D + I) / N  where S=substitutions, D=deletions, I=insertions, N=ref words.
    Uses minimum edit distance on word level.
    """
    def _normalize(text: str) -> list[str]:
        return re.sub(r'[^\w\s]', '', text.lower()).split()

    ref = _normalize(reference)
    hyp = _normalize(hypothesis)
    n = len(ref)
    m = len(hyp)
    if n == 0:
        return 0.0 if m == 0 else 1.0

    # DP table for edit distance
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i-1] == hyp[j-1] else 1
            dp[i][j] = min(
                dp[i-1][j] + 1,      # deletion
                dp[i][j-1] + 1,      # insertion
                dp[i-1][j-1] + cost,  # substitution
            )
    return dp[n][m] / n


# Predefined expected prompts for simulation WER reference.
# These MUST match the prompts in sim_runner.py SCENARIOS so that WER is
# computed correctly when the simulator injects stt_transcript records.
SIM_SCENARIO_PROMPTS = {
    "order_status": [
        "Yes, you can record the call.",
        "Hi, I placed an order last week for some power tools. Can you check the status of my order? The order number is 7 8 4 5 2 3.",
        "Okay thanks. I'm also looking at refrigerators. Do you have any current offers or deals on refrigerators?",
        "What about the Samsung French Door model? Is that on sale?",
        "That sounds good. Can you help me place that order?",
        "No that's all I need. Thank you for your help.",
    ],
    "product_return": [
        "Yes, go ahead and record.",
        "I bought a cordless drill two weeks ago and it stopped working after just a few uses. I'd like to return it.",
        "The order number is 9 3 1 2 0 7. It's a DeWalt 20 volt max cordless drill.",
        "Is it possible to exchange it for a different model instead of getting a refund?",
        "What about the Milwaukee M18 Fuel? Do you have that in stock?",
        "Yes, let's do the exchange. Can you set that up for me?",
        "That's everything. Thanks for your help.",
    ],
    "appliance_install": [
        "Sure, you can record this call.",
        "I'm looking to buy a new washer and dryer set. Do you offer installation services?",
        "How much does the installation typically cost? And does it include removing the old appliances?",
        "What brands do you carry for front load washers? I'm looking for something energy efficient.",
        "The LG WashTower looks interesting. What's the price on that?",
        "How soon could you deliver and install it if I order today?",
        "Okay let me think about it. That's all for now, thank you.",
    ],
    "paint_guidance": [
        "Yes, that's fine.",
        "I'm repainting my master bedroom and I need some help choosing the right paint.",
        "The room is about 14 feet by 12 feet with 9 foot ceilings. How much paint would I need?",
        "What's the difference between eggshell and satin finish? Which one do you recommend for a bedroom?",
        "I'm thinking of a light grey or blue tone. Do you have any popular colors to suggest?",
        "Do you carry Sherwin Williams or just Valspar and HGTV brands?",
        "Great, I'll come into the store to look at samples. Thanks!",
    ],
    "flooring_consult": [
        "Go ahead and record.",
        "I need new flooring for my kitchen. What options do you recommend for a high traffic area?",
        "What's the price difference between luxury vinyl plank and ceramic tile for about 200 square feet?",
        "Is the vinyl plank waterproof? I'm worried about spills and moisture in the kitchen.",
        "Do you offer installation for flooring or is it a do it yourself situation only?",
        "How long does a typical kitchen flooring installation take?",
        "That sounds reasonable. Let me measure my kitchen and I'll call back. Thank you.",
    ],
}
# Flat list combining all prompts for backward compatibility
SIM_EXPECTED_PROMPTS = SIM_SCENARIO_PROMPTS["order_status"]

os.environ["SSL_CERT_FILE"] = certifi.where()

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env.local")

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from livekit import api as lk_api

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")

TELEMETRY_DIR = Path(__file__).parent.parent / "telemetry"
TELEMETRY_DIR.mkdir(exist_ok=True)

AGENT_PY = Path(__file__).parent.parent / "agent.py"
# Always use the venv Python so subprocesses have all packages available
VENV_PYTHON = Path(__file__).parent.parent / "venv" / "bin" / "python3"
if not VENV_PYTHON.exists():
    VENV_PYTHON = Path(sys.executable)  # fallback to current interpreter

app = FastAPI(title="Voice Agent Benchmark")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track running processes
running_processes: dict[str, dict] = {}  # run_id -> {proc, provider, status, mode, log_lines}
# Store recent log lines for each process
process_logs: dict[str, list] = {}  # run_id -> [log_lines]
MAX_LOG_LINES = 200

SIM_RUNNER = Path(__file__).parent / "sim_runner.py"


class BenchmarkRequest(BaseModel):
    provider: str  # "nemo" or "deep"
    num_runs: int = 1


class SimulateRequest(BaseModel):
    provider: str  # "nemo", "deep", or "both"
    num_runs: int = 1
    mute_mic: bool = True  # Disable mic to prevent TTS audio loopback
    scenario: str = "order_status"  # Scenario ID from SIM_SCENARIO_PROMPTS


class MultiRunRequest(BaseModel):
    num_runs_per_provider: int = 1


class LiveRunRequest(BaseModel):
    provider: str  # "nemo" or "deep"


# ── Launch / stop agent runs ────────────────────────────────────────────────

@app.post("/api/benchmark/start")
async def start_benchmark(req: BenchmarkRequest):
    """Start a single agent run in console mode with the given provider."""
    if req.provider not in ("nemo", "deep"):
        raise HTTPException(400, "provider must be 'nemo' or 'deep'")

    run_id = f"{req.provider}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

    env = os.environ.copy()
    env["AGENT_PROVIDER"] = req.provider
    env.pop("MUTE_MIC", None)  # Ensure STT is enabled for manual runs

    proc = subprocess.Popen(
        [str(VENV_PYTHON), str(AGENT_PY), "--provider", req.provider, "console"],
        cwd=str(AGENT_PY.parent),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    running_processes[run_id] = {
        "proc": proc, "provider": req.provider,
        "status": "running", "mode": "console", "pid": proc.pid,
    }
    return {"status": "started", "run_id": run_id, "pid": proc.pid}


@app.post("/api/benchmark/start-live")
async def start_live_benchmark(req: LiveRunRequest):
    """Start agent in dev mode and return a LiveKit token for the browser to join the room."""
    if req.provider not in ("nemo", "deep"):
        raise HTTPException(400, "provider must be 'nemo' or 'deep'")
    if not LIVEKIT_URL or not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(500, "LiveKit credentials not configured in .env.local")

    # Stop any previously running live agents to avoid dispatch conflicts
    for rid, entry in list(running_processes.items()):
        if entry.get("mode") == "live" and entry.get("status") == "running":
            try:
                entry["proc"].terminate()
                entry["proc"].wait(timeout=3)
            except Exception:
                try:
                    entry["proc"].kill()
                except Exception:
                    pass
            entry["status"] = "stopped"

    run_id = f"live_{req.provider}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    room_name = f"bench-{run_id}"

    env = os.environ.copy()
    env["AGENT_PROVIDER"] = req.provider
    env.pop("MUTE_MIC", None)  # Ensure STT is enabled for live voice sessions

    # Start the agent in dev mode (connects to LiveKit server, waits for participants)
    proc = subprocess.Popen(
        [str(VENV_PYTHON), str(AGENT_PY), "--provider", req.provider, "dev"],
        cwd=str(AGENT_PY.parent),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    running_processes[run_id] = {
        "proc": proc, "provider": req.provider,
        "status": "running", "mode": "live", "pid": proc.pid,
        "room": room_name,
        "start_time": time.time(),
    }
    process_logs[run_id] = []

    # Background thread to capture agent logs
    def _stream_logs():
        try:
            for line in iter(proc.stdout.readline, ""):
                if not line:
                    break
                line = line.rstrip()
                logs = process_logs.get(run_id, [])
                logs.append(line)
                if len(logs) > MAX_LOG_LINES:
                    logs.pop(0)
        except Exception:
            pass
        proc.wait()
        entry = running_processes.get(run_id)
        if entry:
            entry["status"] = "completed" if proc.returncode == 0 else "error"

    t = threading.Thread(target=_stream_logs, daemon=True)
    t.start()

    # Generate a participant token for the browser user
    token = (
        lk_api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(f"bench-user-{int(time.time())}")
        .with_name("Benchmark User")
        .with_grants(lk_api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        ))
    )

    return {
        "status": "started",
        "run_id": run_id,
        "pid": proc.pid,
        "room": room_name,
        "token": token.to_jwt(),
        "livekit_url": LIVEKIT_URL,
    }


@app.get("/api/telemetry/live/{run_id}")
async def live_metrics(run_id: str):
    """Return real-time metrics for a currently running session by tailing the telemetry file."""
    # Find matching telemetry file (run_id embedded in the file name may differ slightly)
    # The agent writes to telemetry/<provider>_<timestamp>.jsonl
    candidates = list(TELEMETRY_DIR.glob("*.jsonl"))
    # Sort by mtime descending, look for the freshest file matching the provider
    entry = running_processes.get(run_id)
    provider = entry["provider"] if entry else run_id.split("_")[1] if "_" in run_id else ""

    # Only consider files whose first record was written after this live session started.
    # This prevents stale simulation telemetry files from being picked up.
    start_time = entry.get("start_time", 0) if entry else 0

    best = None
    best_mtime = 0
    for f in candidates:
        if not f.stem.startswith(provider):
            continue
        fstat = f.stat()
        if fstat.st_mtime <= best_mtime:
            continue
        # Read the first record's timestamp to verify the file belongs to this session
        if start_time > 0:
            try:
                with open(f) as fh:
                    first_line = fh.readline().strip()
                    if first_line:
                        first_ts = json.loads(first_line).get("timestamp", 0)
                        if first_ts < start_time:
                            continue  # file predates this live session
            except Exception:
                continue
        best = f
        best_mtime = fstat.st_mtime

    if not best:
        return {"metrics": [], "transcripts": []}

    metrics_out = []
    transcripts = []
    try:
        with open(best) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                mt = rec.get("metric_type", "")
                if mt == "stt_transcript" and rec.get("source") != "sim_injected":
                    transcripts.append({"text": rec.get("transcript", ""), "role": "user", "time": rec.get("iso_time", "")})
                elif mt == "agent_transcript":
                    transcripts.append({"text": rec.get("transcript", ""), "role": "agent", "time": rec.get("iso_time", "")})
                elif mt in ("llm", "tts", "eou", "ttfa", "turn_rtt", "interruption"):
                    metrics_out.append({
                        "type": mt,
                        "time": rec.get("iso_time", ""),
                        **{k: v for k, v in rec.items() if k not in ("run_id", "provider", "metric_type", "timestamp", "iso_time")},
                    })
    except Exception:
        pass

    return {"metrics": metrics_out[-30:], "transcripts": transcripts}


@app.post("/api/benchmark/simulate")
async def simulate_benchmark(req: SimulateRequest, background_tasks: BackgroundTasks):
    """Launch automated simulated benchmark (no mic required)."""
    if req.provider not in ("nemo", "deep", "both"):
        raise HTTPException(400, "provider must be 'nemo', 'deep', or 'both'")

    # Validate scenario
    scenario_ids = list(SIM_SCENARIO_PROMPTS.keys())
    scenario_id = req.scenario if req.scenario in SIM_SCENARIO_PROMPTS else "order_status"
    scenario_index = scenario_ids.index(scenario_id)

    run_id = f"sim_{req.provider}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

    env = os.environ.copy()
    if req.mute_mic:
        env["MUTE_MIC"] = "1"

    proc = subprocess.Popen(
        [
            str(VENV_PYTHON), str(SIM_RUNNER),
            "--provider", req.provider,
            "--runs", str(req.num_runs),
            "--scenario", str(scenario_index),
        ],
        cwd=str(AGENT_PY.parent),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    running_processes[run_id] = {
        "proc": proc, "provider": req.provider,
        "status": "running", "mode": "simulate", "pid": proc.pid,
    }
    process_logs[run_id] = []

    # Background thread to read stdout and capture logs
    def _stream_logs():
        try:
            for line in iter(proc.stdout.readline, ""):
                if not line:
                    break
                line = line.rstrip()
                logs = process_logs.get(run_id, [])
                logs.append(line)
                if len(logs) > MAX_LOG_LINES:
                    logs.pop(0)
        except Exception:
            pass
        # Mark completed
        proc.wait()
        entry = running_processes.get(run_id)
        if entry:
            entry["status"] = "completed" if proc.returncode == 0 else "error"

    t = threading.Thread(target=_stream_logs, daemon=True)
    t.start()

    return {"status": "started", "run_id": run_id, "pid": proc.pid, "mode": "simulate"}


@app.post("/api/benchmark/stop/{run_id}")
async def stop_benchmark(run_id: str):
    """Stop a running agent process."""
    entry = running_processes.get(run_id)
    if not entry:
        raise HTTPException(404, "Run not found")
    proc = entry["proc"]
    try:
        proc.send_signal(signal.SIGINT)
        proc.wait(timeout=10)
    except Exception:
        proc.kill()
    entry["status"] = "stopped"
    running_processes.pop(run_id, None)
    return {"status": "stopped", "run_id": run_id}


@app.get("/api/benchmark/logs/{run_id}")
async def get_logs(run_id: str, since: int = 0):
    """Get recent log lines for a running/finished process."""
    logs = process_logs.get(run_id, [])
    return {"run_id": run_id, "lines": logs[since:], "total": len(logs)}


@app.get("/api/benchmark/running")
async def list_running():
    """List currently running agent processes."""
    result = {}
    for rid, entry in list(running_processes.items()):
        proc = entry["proc"]
        if proc.poll() is not None:
            # Process finished
            entry["status"] = "completed" if proc.returncode == 0 else "error"
            running_processes.pop(rid, None)
        else:
            result[rid] = {
                "pid": entry["pid"],
                "provider": entry["provider"],
                "mode": entry["mode"],
                "status": entry["status"],
            }
    return result


# ── Scenario listing ──────────────────────────────────────────────────────

@app.get("/api/benchmark/scenarios")
async def list_scenarios():
    """Return available simulation scenarios."""
    return [
        {"id": sid, "name": sid.replace("_", " ").title(), "prompts": len(prompts)}
        for sid, prompts in SIM_SCENARIO_PROMPTS.items()
    ]


# ── ASR Dataset Evaluation ────────────────────────────────────────────────

ASR_EVAL_MODULE = Path(__file__).parent / "asr_eval.py"
ASR_RESULTS_DIR = TELEMETRY_DIR  # reuse same dir

class AsrEvalRequest(BaseModel):
    provider: str = "both"  # "nemo", "deep", "whisper", "both", or "all"
    dataset: str = "librispeech_mini"
    samples: int = 10


@app.get("/api/asr/datasets")
async def list_asr_datasets():
    """Return available ASR evaluation datasets."""
    from benchmark.asr_eval import ALL_DATASETS
    return [
        {"id": d["id"], "name": d["name"], "description": d["description"],
         "total_samples": len(d["samples"])}
        for d in ALL_DATASETS.values()
    ]


@app.post("/api/asr/evaluate")
async def start_asr_evaluation(req: AsrEvalRequest, background_tasks: BackgroundTasks):
    """Launch ASR evaluation as a background process."""
    if req.provider not in ("nemo", "deep", "whisper", "both", "all"):
        raise HTTPException(400, "provider must be 'nemo', 'deep', 'whisper', 'both', or 'all'")

    run_id = f"asr_{req.provider}_{req.dataset}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

    proc = subprocess.Popen(
        [
            str(VENV_PYTHON), str(ASR_EVAL_MODULE),
            "--provider", req.provider,
            "--dataset", req.dataset,
            "--samples", str(req.samples),
        ],
        cwd=str(AGENT_PY.parent),
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    running_processes[run_id] = {
        "proc": proc, "provider": req.provider,
        "status": "running", "mode": "asr_eval", "pid": proc.pid,
    }
    process_logs[run_id] = []

    def _stream_logs():
        try:
            for line in iter(proc.stdout.readline, ""):
                if not line:
                    break
                line = line.rstrip()
                logs = process_logs.get(run_id, [])
                logs.append(line)
                if len(logs) > MAX_LOG_LINES:
                    logs.pop(0)
        except Exception:
            pass
        proc.wait()
        entry = running_processes.get(run_id)
        if entry:
            entry["status"] = "completed" if proc.returncode == 0 else "error"

    threading.Thread(target=_stream_logs, daemon=True).start()

    return {"status": "started", "run_id": run_id, "pid": proc.pid}


@app.get("/api/asr/results")
async def list_asr_results():
    """Return all ASR evaluation results."""
    results = []
    for f in sorted(ASR_RESULTS_DIR.glob("asr_*.json"), reverse=True):
        try:
            with open(f) as fh:
                data = json.load(fh)
                results.append({
                    "file": f.name,
                    "provider": data.get("provider"),
                    "model_name": data.get("model_name"),
                    "dataset_id": data.get("dataset_id"),
                    "dataset_name": data.get("dataset_name"),
                    "avg_wer": data.get("avg_wer"),
                    "min_wer": data.get("min_wer"),
                    "max_wer": data.get("max_wer"),
                    "evaluated": data.get("evaluated"),
                    "total_samples": data.get("total_samples"),
                    "cold_start_ms": data.get("cold_start_ms"),
                    "avg_warm_ms": data.get("avg_warm_ms"),
                    "avg_latency_ms": data.get("avg_latency_ms"),
                    "avg_rtf": data.get("avg_rtf"),
                    "min_rtf": data.get("min_rtf"),
                    "max_rtf": data.get("max_rtf"),
                    "timestamp": data.get("timestamp"),
                    "results": data.get("results", []),
                })
        except Exception:
            continue
    return results


# ── Telemetry data endpoints ────────────────────────────────────────────────

def _filtered_telemetry_files(date_from: Optional[str] = None, date_to: Optional[str] = None) -> list[Path]:
    """Return telemetry .jsonl files filtered by optional date range (ISO date strings)."""
    files = list(TELEMETRY_DIR.glob("*.jsonl"))
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
            ts_from = dt_from.timestamp()
            files = [f for f in files if f.stat().st_mtime >= ts_from]
        except (ValueError, OSError):
            pass
    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
            ts_to = dt_to.timestamp()
            files = [f for f in files if f.stat().st_mtime <= ts_to]
        except (ValueError, OSError):
            pass
    return files


@app.get("/api/telemetry/runs")
async def list_runs(date_from: Optional[str] = None, date_to: Optional[str] = None):
    """List all telemetry run files."""
    runs = []
    for f in sorted(_filtered_telemetry_files(date_from, date_to), key=lambda x: x.stat().st_mtime, reverse=True):
        # Parse first line to get provider
        provider = "unknown"
        metric_count = 0
        try:
            with open(f) as fh:
                lines = fh.readlines()
                metric_count = len(lines)
                if lines:
                    first = json.loads(lines[0])
                    provider = first.get("provider", "unknown")
        except Exception:
            pass
        runs.append({
            "run_id": f.stem,
            "file": f.name,
            "provider": provider,
            "metric_count": metric_count,
            "modified": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
        })
    return runs


@app.get("/api/telemetry/run/{run_id}")
async def get_run(run_id: str):
    """Get all metrics for a specific run."""
    path = TELEMETRY_DIR / f"{run_id}.jsonl"
    if not path.exists():
        raise HTTPException(404, "Run not found")
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


@app.get("/api/telemetry/compare")
async def compare_providers(date_from: Optional[str] = None, date_to: Optional[str] = None):
    """Aggregate and compare metrics across all nemo vs deep runs."""
    provider_metrics = defaultdict(lambda: {
        "llm_ttft": [],
        "llm_tokens_per_second": [],
        "eou_delay": [],
        "eou_transcription_delay": [],
        "tts_ttfb": [],
        "ttfa": [],
        "turn_rtt": [],
        "session_durations": [],
        "interruption_counts": [],
        "turn_counts": [],
        "run_count": 0,
        "runs": [],
    })

    for f in _filtered_telemetry_files(date_from, date_to):
        run_id = f.stem
        provider = run_id.split("_")[0] if "_" in run_id else "unknown"

        with open(f) as fh:
            run_has_data = False
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                p = rec.get("provider", provider)
                bucket = provider_metrics[p]

                mt = rec.get("metric_type", "")
                if mt == "llm":
                    if rec.get("ttft") is not None:
                        bucket["llm_ttft"].append(rec["ttft"])
                    if rec.get("tokens_per_second") is not None:
                        bucket["llm_tokens_per_second"].append(rec["tokens_per_second"])
                    run_has_data = True
                elif mt == "eou":
                    if rec.get("end_of_utterance_delay") is not None:
                        bucket["eou_delay"].append(rec["end_of_utterance_delay"])
                    if rec.get("transcription_delay") is not None:
                        bucket["eou_transcription_delay"].append(rec["transcription_delay"])
                    run_has_data = True
                elif mt == "tts":
                    if rec.get("ttfb") is not None:
                        bucket["tts_ttfb"].append(rec["ttfb"])
                    run_has_data = True
                elif mt == "ttfa":
                    if rec.get("ttfa") is not None:
                        bucket["ttfa"].append(rec["ttfa"])
                    run_has_data = True
                elif mt == "turn_rtt":
                    if rec.get("turn_rtt") is not None:
                        bucket["turn_rtt"].append(rec["turn_rtt"])
                elif mt == "usage_summary":
                    if rec.get("session_duration") is not None:
                        bucket["session_durations"].append(rec["session_duration"])
                    if rec.get("interruption_count") is not None:
                        bucket["interruption_counts"].append(rec["interruption_count"])
                    if rec.get("turn_count") is not None:
                        bucket["turn_counts"].append(rec["turn_count"])

            if run_has_data:
                provider_metrics[provider]["run_count"] += 1
                provider_metrics[provider]["runs"].append(run_id)

    def _stats(vals):
        if not vals:
            return {"avg": None, "min": None, "max": None, "p50": None, "p95": None, "count": 0}
        s = sorted(vals)
        n = len(s)
        return {
            "avg": round(sum(s) / n, 4),
            "min": round(s[0], 4),
            "max": round(s[-1], 4),
            "p50": round(s[n // 2], 4),
            "p95": round(s[int(n * 0.95)], 4),
            "count": n,
        }

    result = {}
    for provider, data in provider_metrics.items():
        result[provider] = {
            "run_count": data["run_count"],
            "runs": data["runs"],
            "llm_ttft": _stats(data["llm_ttft"]),
            "llm_tokens_per_second": _stats(data["llm_tokens_per_second"]),
            "eou_delay": _stats(data["eou_delay"]),
            "eou_transcription_delay": _stats(data["eou_transcription_delay"]),
            "tts_ttfb": _stats(data["tts_ttfb"]),
            "ttfa": _stats(data["ttfa"]),
            "turn_rtt": _stats(data["turn_rtt"]),
            "session_duration": _stats(data["session_durations"]),
            "interruption_rate": {
                "total_interruptions": sum(data["interruption_counts"]),
                "total_turns": sum(data["turn_counts"]),
                "rate": round(sum(data["interruption_counts"]) / max(sum(data["turn_counts"]), 1), 4),
            },
        }
    return result


@app.get("/api/telemetry/trend")
async def telemetry_trend(date_from: Optional[str] = None, date_to: Optional[str] = None):
    """Return per-run metrics for trend analysis."""
    runs = []
    for f in sorted(_filtered_telemetry_files(date_from, date_to), key=lambda x: x.stat().st_mtime):
        run_id = f.stem
        provider = run_id.split("_")[0] if "_" in run_id else "unknown"
        run_data = {
            "run_id": run_id,
            "provider": provider,
            "timestamp": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
            "llm_ttft": [], "llm_tps": [],
            "eou_delay": [], "tts_ttfb": [], "ttfa": [],
            "turn_rtt": [],
            "prompt_tokens": 0, "completion_tokens": 0, "tts_characters": 0,
            "session_duration": None, "turn_count": 0, "interruption_count": 0,
            "stt_transcripts": [],
        }
        try:
            with open(f) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    mt = rec.get("metric_type", "")
                    if mt == "llm":
                        if rec.get("ttft") is not None:
                            run_data["llm_ttft"].append(rec["ttft"])
                        if rec.get("tokens_per_second") is not None:
                            run_data["llm_tps"].append(rec["tokens_per_second"])
                        run_data["prompt_tokens"] += rec.get("prompt_tokens", 0)
                        run_data["completion_tokens"] += rec.get("completion_tokens", 0)
                    elif mt == "eou":
                        if rec.get("end_of_utterance_delay") is not None:
                            run_data["eou_delay"].append(rec["end_of_utterance_delay"])
                    elif mt == "tts":
                        if rec.get("ttfb") is not None:
                            run_data["tts_ttfb"].append(rec["ttfb"])
                    elif mt == "ttfa":
                        if rec.get("ttfa") is not None:
                            run_data["ttfa"].append(rec["ttfa"])
                    elif mt == "turn_rtt":
                        if rec.get("turn_rtt") is not None:
                            run_data["turn_rtt"].append(rec["turn_rtt"])
                    elif mt == "stt_transcript":
                        if rec.get("transcript"):
                            run_data["stt_transcripts"].append(rec["transcript"])
                            if rec.get("scenario_id"):
                                run_data["scenario_id"] = rec["scenario_id"]
                    elif mt == "usage_summary":
                        run_data["prompt_tokens"] = max(run_data["prompt_tokens"], rec.get("llm_prompt_tokens", 0))
                        run_data["completion_tokens"] = max(run_data["completion_tokens"], rec.get("llm_completion_tokens", 0))
                        run_data["tts_characters"] = max(run_data["tts_characters"], rec.get("tts_characters_count", 0))
                        run_data["session_duration"] = rec.get("session_duration")
                        run_data["turn_count"] = rec.get("turn_count", 0)
                        run_data["interruption_count"] = rec.get("interruption_count", 0)
        except Exception:
            continue

        # Compute averages
        for key in ["llm_ttft", "llm_tps", "eou_delay", "tts_ttfb", "ttfa", "turn_rtt"]:
            vals = run_data[key]
            run_data[f"{key}_avg"] = round(sum(vals) / len(vals), 4) if vals else None
            run_data[f"{key}_count"] = len(vals)
            del run_data[key]

        # Compute WER if we have transcripts
        transcripts = run_data.pop("stt_transcripts", [])
        scenario_id = run_data.pop("scenario_id", "order_status")
        ref_prompts = SIM_SCENARIO_PROMPTS.get(scenario_id, SIM_EXPECTED_PROMPTS)
        if transcripts and len(transcripts) > 0:
            wer_scores = []
            for i, hyp in enumerate(transcripts):
                if i < len(ref_prompts):
                    wer = _compute_wer(ref_prompts[i], hyp)
                    wer_scores.append(wer)
            run_data["wer_avg"] = round(sum(wer_scores) / len(wer_scores), 4) if wer_scores else None
            run_data["wer_count"] = len(wer_scores)
        else:
            run_data["wer_avg"] = None
            run_data["wer_count"] = 0

        runs.append(run_data)
    return runs


@app.get("/api/telemetry/wer")
async def telemetry_wer(date_from: Optional[str] = None, date_to: Optional[str] = None):
    """Detailed WER analysis per provider with per-utterance breakdown."""
    provider_wer = defaultdict(lambda: {"runs": [], "all_wer": []})

    for f in sorted(_filtered_telemetry_files(date_from, date_to), key=lambda x: x.stat().st_mtime):
        run_id = f.stem
        provider = run_id.split("_")[0] if "_" in run_id else "unknown"
        transcripts = []
        scenario_id = "order_status"
        try:
            with open(f) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    if rec.get("metric_type") == "stt_transcript" and rec.get("transcript"):
                        transcripts.append(rec["transcript"])
                        if rec.get("scenario_id"):
                            scenario_id = rec["scenario_id"]
        except Exception:
            continue

        if not transcripts:
            continue

        ref_prompts = SIM_SCENARIO_PROMPTS.get(scenario_id, SIM_EXPECTED_PROMPTS)
        utterances = []
        for i, hyp in enumerate(transcripts):
            ref = ref_prompts[i] if i < len(ref_prompts) else None
            wer = _compute_wer(ref, hyp) if ref else None
            utterances.append({
                "index": i,
                "reference": ref,
                "hypothesis": hyp,
                "wer": round(wer, 4) if wer is not None else None,
            })
            if wer is not None:
                provider_wer[provider]["all_wer"].append(wer)

        avg_wer = None
        wer_vals = [u["wer"] for u in utterances if u["wer"] is not None]
        if wer_vals:
            avg_wer = round(sum(wer_vals) / len(wer_vals), 4)
        provider_wer[provider]["runs"].append({
            "run_id": run_id, "avg_wer": avg_wer, "utterances": utterances,
        })

    result = {}
    for prov, data in provider_wer.items():
        all_w = data["all_wer"]
        result[prov] = {
            "overall_wer": round(sum(all_w) / len(all_w), 4) if all_w else None,
            "total_utterances": len(all_w),
            "runs": data["runs"],
        }
    return result


@app.get("/api/telemetry/usage")
async def telemetry_usage(date_from: Optional[str] = None, date_to: Optional[str] = None):
    """Return token/usage data per provider for gauge views."""
    provider_usage = defaultdict(lambda: {
        "prompt_tokens": 0, "completion_tokens": 0,
        "tts_characters": 0, "run_count": 0,
        "total_session_duration": 0, "total_turns": 0,
        "total_interruptions": 0,
    })
    for f in _filtered_telemetry_files(date_from, date_to):
        run_id = f.stem
        provider = run_id.split("_")[0] if "_" in run_id else "unknown"
        try:
            with open(f) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    mt = rec.get("metric_type", "")
                    if mt == "usage_summary":
                        provider_usage[provider]["prompt_tokens"] += rec.get("llm_prompt_tokens", 0)
                        provider_usage[provider]["completion_tokens"] += rec.get("llm_completion_tokens", 0)
                        provider_usage[provider]["tts_characters"] += rec.get("tts_characters_count", 0)
                        provider_usage[provider]["total_session_duration"] += rec.get("session_duration", 0)
                        provider_usage[provider]["total_turns"] += rec.get("turn_count", 0)
                        provider_usage[provider]["total_interruptions"] += rec.get("interruption_count", 0)
                        provider_usage[provider]["run_count"] += 1
        except Exception:
            continue
    return dict(provider_usage)


@app.delete("/api/telemetry/clear")
async def clear_telemetry():
    """Delete all telemetry files."""
    count = 0
    for f in TELEMETRY_DIR.glob("*.jsonl"):
        f.unlink()
        count += 1
    return {"deleted": count}


# Serve the UI
UI_DIR = Path(__file__).parent / "ui"
if UI_DIR.exists():
    app.mount("/", StaticFiles(directory=str(UI_DIR), html=True), name="ui")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8089)
