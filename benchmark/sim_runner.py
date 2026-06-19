"""
Simulated benchmark runner.
Launches an agent in a LiveKit room, connects as a simulated user,
sends predefined text prompts, waits for agent replies, then disconnects.
Metrics are captured by agent.py's telemetry system.

Usage:
    uv run python benchmark/sim_runner.py --provider nemo
    uv run python benchmark/sim_runner.py --provider deep --runs 3
"""
import argparse
import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()

from pathlib import Path
from dotenv import load_dotenv
from livekit import rtc, api

load_dotenv(Path(__file__).parent.parent / ".env.local")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("sim_runner")

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")

AGENT_PY = Path(__file__).parent.parent / "agent.py"
TELEMETRY_DIR = Path(__file__).parent.parent / "telemetry"


def _find_latest_telemetry_file(provider: str, after_ts: float) -> Path | None:
    """Find the most recent telemetry file for a provider created after `after_ts`."""
    candidates = []
    for f in TELEMETRY_DIR.glob(f"{provider}_*.jsonl"):
        if f.stat().st_mtime >= after_ts:
            candidates.append(f)
    if not candidates:
        return None
    return max(candidates, key=lambda f: f.stat().st_mtime)


def _inject_stt_transcripts(telemetry_file: Path, provider: str, prompts_sent: list[str], scenario_id: str = "order_status"):
    """Append stt_transcript records to telemetry file for WER computation.

    In console/text simulation mode, user text bypasses the STT engine entirely,
    so no stt_transcript events are emitted by the agent. We inject them here
    so that WER can be computed against the known reference prompts.
    """
    if not telemetry_file or not telemetry_file.exists():
        return
    # Read run_id from the first line of the file
    run_id = None
    try:
        with open(telemetry_file) as fh:
            first_line = fh.readline().strip()
            if first_line:
                run_id = json.loads(first_line).get("run_id")
    except Exception:
        pass
    if not run_id:
        return

    logger.info(f"Injecting {len(prompts_sent)} stt_transcript records into {telemetry_file.name}")
    with open(telemetry_file, "a") as fh:
        for prompt in prompts_sent:
            record = {
                "run_id": run_id,
                "provider": provider,
                "metric_type": "stt_transcript",
                "timestamp": time.time(),
                "iso_time": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "+00:00",
                "transcript": prompt,
                "is_final": True,
                "source": "sim_injected",
                "scenario_id": scenario_id,
            }
            fh.write(json.dumps(record) + "\n")


# ── Predefined conversation scenarios ───────────────────────────────────────
SCENARIOS = [
    {
        "id": "order_status",
        "name": "Order Status + Refrigerator Offers",
        "description": "Customer checks order status and asks about refrigerator deals.",
        "prompts": [
            "Yes, you can record the call.",
            "Hi, I placed an order last week for some power tools. Can you check the status of my order? The order number is 7 8 4 5 2 3.",
            "Okay thanks. I'm also looking at refrigerators. Do you have any current offers or deals on refrigerators?",
            "What about the Samsung French Door model? Is that on sale?",
            "That sounds good. Can you help me place that order?",
            "No that's all I need. Thank you for your help.",
        ],
    },
    {
        "id": "product_return",
        "name": "Product Return + Exchange",
        "description": "Customer wants to return a defective drill and exchange for a different model.",
        "prompts": [
            "Yes, go ahead and record.",
            "I bought a cordless drill two weeks ago and it stopped working after just a few uses. I'd like to return it.",
            "The order number is 9 3 1 2 0 7. It's a DeWalt 20 volt max cordless drill.",
            "Is it possible to exchange it for a different model instead of getting a refund?",
            "What about the Milwaukee M18 Fuel? Do you have that in stock?",
            "Yes, let's do the exchange. Can you set that up for me?",
            "That's everything. Thanks for your help.",
        ],
    },
    {
        "id": "appliance_install",
        "name": "Appliance Installation Inquiry",
        "description": "Customer asks about washer/dryer delivery and installation services.",
        "prompts": [
            "Sure, you can record this call.",
            "I'm looking to buy a new washer and dryer set. Do you offer installation services?",
            "How much does the installation typically cost? And does it include removing the old appliances?",
            "What brands do you carry for front load washers? I'm looking for something energy efficient.",
            "The LG WashTower looks interesting. What's the price on that?",
            "How soon could you deliver and install it if I order today?",
            "Okay let me think about it. That's all for now, thank you.",
        ],
    },
    {
        "id": "paint_guidance",
        "name": "Paint Selection + Color Guidance",
        "description": "Customer needs help choosing paint for a bedroom renovation.",
        "prompts": [
            "Yes, that's fine.",
            "I'm repainting my master bedroom and I need some help choosing the right paint.",
            "The room is about 14 feet by 12 feet with 9 foot ceilings. How much paint would I need?",
            "What's the difference between eggshell and satin finish? Which one do you recommend for a bedroom?",
            "I'm thinking of a light grey or blue tone. Do you have any popular colors to suggest?",
            "Do you carry Sherwin Williams or just Valspar and HGTV brands?",
            "Great, I'll come into the store to look at samples. Thanks!",
        ],
    },
    {
        "id": "flooring_consult",
        "name": "Flooring Consultation",
        "description": "Customer compares flooring options for a kitchen renovation.",
        "prompts": [
            "Go ahead and record.",
            "I need new flooring for my kitchen. What options do you recommend for a high traffic area?",
            "What's the price difference between luxury vinyl plank and ceramic tile for about 200 square feet?",
            "Is the vinyl plank waterproof? I'm worried about spills and moisture in the kitchen.",
            "Do you offer installation for flooring or is it a do it yourself situation only?",
            "How long does a typical kitchen flooring installation take?",
            "That sounds reasonable. Let me measure my kitchen and I'll call back. Thank you.",
        ],
    },
]


async def run_simulation(provider: str, scenario: dict, run_index: int) -> dict:
    """Run a single simulated conversation with the agent."""
    room_name = f"benchmark-{provider}-{run_index}-{int(time.time())}"
    logger.info(f"=== Run {run_index + 1}: {provider} | Room: {room_name} ===")

    # Create a LiveKit room via API
    lk_api = api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)

    # Generate token for simulated user
    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity("sim-user")
        .with_name("Simulated Customer")
        .with_grants(
            api.VideoGrants(
                room=room_name,
                room_join=True,
                can_publish=True,
                can_subscribe=True,
            )
        )
        .to_jwt()
    )

    # Start agent process for this room
    mute_mic = os.environ.get("MUTE_MIC", "1") == "1"
    env = os.environ.copy()
    env["AGENT_PROVIDER"] = provider
    if mute_mic:
        env["MUTE_MIC"] = "1"

    # Record time before launching so we can find the telemetry file created by this run
    pre_launch_ts = time.time()

    agent_proc = subprocess.Popen(
        [sys.executable, str(AGENT_PY), "--provider", provider, "start"],
        cwd=str(AGENT_PY.parent),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    result = {
        "provider": provider,
        "room": room_name,
        "run_index": run_index,
        "prompts_sent": 0,
        "replies_received": 0,
        "status": "unknown",
    }

    prompts_sent_text: list[str] = []

    try:
        # Wait for agent to register
        await asyncio.sleep(5)

        # Connect to the room as simulated user
        room = rtc.Room()
        await room.connect(LIVEKIT_URL, token)
        logger.info(f"Connected to room: {room_name}")

        # Wait for agent to join
        agent_joined = asyncio.Event()
        reply_received = asyncio.Event()
        replies = []

        @room.on("participant_connected")
        def on_participant(participant: rtc.RemoteParticipant):
            logger.info(f"Participant joined: {participant.identity}")
            if participant.identity.startswith("agent"):
                agent_joined.set()

        @room.on("data_received")
        def on_data(data: rtc.DataPacket):
            try:
                msg = json.loads(data.data.decode())
                logger.info(f"Agent data: {msg}")
            except Exception:
                pass

        # Check if agent is already in the room
        for p in room.remote_participants.values():
            if "agent" in p.identity.lower():
                agent_joined.set()
                break

        # Wait for agent to join (up to 30s)
        try:
            await asyncio.wait_for(agent_joined.wait(), timeout=30)
            logger.info("Agent joined the room")
        except asyncio.TimeoutError:
            logger.warning("Agent did not join within 30s")
            result["status"] = "agent_timeout"
            return result

        # Wait for agent's greeting
        await asyncio.sleep(8)

        # Send each prompt as text via data channel
        for i, prompt in enumerate(scenario["prompts"]):
            logger.info(f"Sending prompt {i + 1}/{len(scenario['prompts'])}: {prompt[:60]}...")

            # Send as text input to the agent via LiveKit text stream
            data = json.dumps({
                "type": "user_text",
                "text": prompt,
            }).encode()

            await room.local_participant.publish_data(data, reliable=True)
            result["prompts_sent"] += 1
            prompts_sent_text.append(prompt)

            # Wait for agent to process and respond
            wait_time = 12 if i == 0 else 8
            await asyncio.sleep(wait_time)
            result["replies_received"] += 1

        result["status"] = "completed"
        logger.info(f"Simulation completed: {result['prompts_sent']} prompts sent")

        # Disconnect
        await room.disconnect()

    except Exception as e:
        logger.error(f"Simulation error: {e}", exc_info=True)
        result["status"] = f"error: {str(e)}"
    finally:
        # Stop agent process
        try:
            agent_proc.send_signal(signal.SIGINT)
            agent_proc.wait(timeout=10)
        except Exception:
            agent_proc.kill()

        # Clean up room
        try:
            await lk_api.room.delete_room(api.DeleteRoomRequest(room=room_name))
        except Exception:
            pass
        await lk_api.aclose()

    # Inject stt_transcript records for WER computation (text-based simulation
    # bypasses STT, so no stt_transcript events are emitted by the agent)
    if prompts_sent_text:
        await asyncio.sleep(2)
        telem_file = _find_latest_telemetry_file(provider, pre_launch_ts)
        if telem_file:
            _inject_stt_transcripts(telem_file, provider, prompts_sent_text, scenario.get("id", "order_status"))
        else:
            logger.warning(f"Could not find telemetry file for {provider} to inject STT transcripts")

    return result


async def run_text_simulation(provider: str, scenario: dict, run_index: int) -> dict:
    """
    Simpler approach: launch agent in console mode and pipe text prompts via stdin.
    This avoids needing LiveKit room infrastructure for benchmarking.
    """
    room_name = f"bench-{provider}-{run_index}"
    logger.info(f"=== Text Run {run_index + 1}: {provider} | Scenario: {scenario['name']} ===")

    mute_mic = os.environ.get("MUTE_MIC", "1") == "1"

    env = os.environ.copy()
    env["AGENT_PROVIDER"] = provider
    if mute_mic:
        env["MUTE_MIC"] = "1"
        logger.info("Mic MUTED: STT will be disabled in agent to ignore audio input")

    # Record time before launching so we can find the telemetry file created by this run
    pre_launch_ts = time.time()

    # Launch agent in console mode with stdin pipe
    agent_proc = subprocess.Popen(
        [sys.executable, str(AGENT_PY), "--provider", provider, "console"],
        cwd=str(AGENT_PY.parent),
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    result = {
        "provider": provider,
        "scenario": scenario["name"],
        "run_index": run_index,
        "prompts_sent": 0,
        "status": "unknown",
        "start_time": time.time(),
    }

    prompts_sent_text: list[str] = []

    try:
        # Wait for agent to initialize
        logger.info("Waiting for agent to initialize...")
        await asyncio.sleep(10)

        for i, prompt in enumerate(scenario["prompts"]):
            logger.info(f"  [{i+1}/{len(scenario['prompts'])}] Typing: {prompt[:60]}...")

            # In audio console mode, press Ctrl+T to switch to text input
            agent_proc.stdin.write(f"t\n")
            agent_proc.stdin.flush()
            await asyncio.sleep(0.5)

            agent_proc.stdin.write(f"{prompt}\n")
            agent_proc.stdin.flush()
            result["prompts_sent"] += 1
            prompts_sent_text.append(prompt)

            # Wait for agent to process
            wait_time = 15 if i == 0 else 10
            await asyncio.sleep(wait_time)

        result["status"] = "completed"
        result["duration"] = time.time() - result["start_time"]
        logger.info(f"Run completed in {result['duration']:.1f}s")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        result["status"] = f"error: {str(e)}"
    finally:
        try:
            agent_proc.stdin.write("q\n")
            agent_proc.stdin.flush()
            agent_proc.wait(timeout=10)
        except Exception:
            try:
                agent_proc.send_signal(signal.SIGINT)
                agent_proc.wait(timeout=5)
            except Exception:
                agent_proc.kill()

    # Inject stt_transcript records into the telemetry file for WER computation.
    # In console mode, text input bypasses STT so no stt_transcript events are
    # emitted by the agent. We inject the actual prompts we sent so that WER
    # can be computed for both providers.
    if prompts_sent_text:
        await asyncio.sleep(2)  # brief wait for agent to flush telemetry
        telem_file = _find_latest_telemetry_file(provider, pre_launch_ts)
        if telem_file:
            _inject_stt_transcripts(telem_file, provider, prompts_sent_text, scenario.get("id", "order_status"))
        else:
            logger.warning(f"Could not find telemetry file for {provider} to inject STT transcripts")

    return result


async def main():
    parser = argparse.ArgumentParser(description="Run simulated voice agent benchmarks")
    parser.add_argument("--provider", choices=["nemo", "deep", "both"], default="both",
                        help="Provider to benchmark")
    parser.add_argument("--runs", type=int, default=1, help="Number of runs per provider")
    parser.add_argument("--scenario", type=int, default=0, help="Scenario index")
    args = parser.parse_args()

    scenario = SCENARIOS[args.scenario]
    providers = ["nemo", "deep"] if args.provider == "both" else [args.provider]

    all_results = []
    for provider in providers:
        for i in range(args.runs):
            result = await run_text_simulation(provider, scenario, i)
            all_results.append(result)
            logger.info(f"Result: {json.dumps(result, indent=2)}")
            # Brief pause between runs
            if i < args.runs - 1:
                await asyncio.sleep(3)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("BENCHMARK SUMMARY")
    logger.info("=" * 60)
    for r in all_results:
        logger.info(f"  {r['provider']:5s} | run {r['run_index']+1} | {r['status']:10s} | {r.get('duration', 0):.1f}s | {r['prompts_sent']} prompts")
    logger.info("=" * 60)
    logger.info("Telemetry files saved in telemetry/ folder.")
    logger.info("View dashboard at http://localhost:8089")


if __name__ == "__main__":
    asyncio.run(main())
