from asyncio import Server
import argparse
import json
import logging
import os
import certifi
import time
import httpx
from datetime import datetime, timezone
from pathlib import Path

os.environ["SSL_CERT_FILE"] = certifi.where()

from dotenv import load_dotenv
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents import llm,stt,tts, room_io
from livekit.agents.llm import FallbackAdapter
from livekit.agents import AgentStateChangedEvent, MetricsCollectedEvent, metrics
from livekit.agents import UserInputTranscribedEvent, UserStateChangedEvent
from livekit.agents import ConversationItemAddedEvent
from livekit.agents import function_tool, RunContext, ToolError
from livekit.agents import mcp
from livekit.agents import AgentTask
from livekit import api

from livekit.agents import (
    Agent,
    AgentSession,
    AgentServer,
    JobContext,
    RoomInputOptions,
    WorkerOptions,
    cli,
)
from livekit.plugins import deepgram, noise_cancellation, openai, silero, nvidia

logger = logging.getLogger("agent")
vad = silero.VAD.load()

load_dotenv(".env.local")

outbound_trunk_id = os.getenv("OUTBOUND_TRUNK_ID")
nvidia_api_key = os.getenv("NVIDIA_API_KEY", "")

# ---------------------------------------------------------------------------
# Provider switch: "nemo" (NVIDIA Nemotron) vs "deep" (Deepgram + OpenAI)
# Set via AGENT_PROVIDER env var or --provider CLI arg (see bottom of file)
# ---------------------------------------------------------------------------
AGENT_PROVIDER = os.getenv("AGENT_PROVIDER", "nemo").lower()
MUTE_MIC = os.getenv("MUTE_MIC", "0") == "1"

def get_stt():
    if AGENT_PROVIDER == "deep":
        return deepgram.STT()
    return nvidia.STT(language_code="en-US", api_key=nvidia_api_key)

def get_llm():
    if AGENT_PROVIDER == "deep":
        primary = openai.LLM(model="gpt-4o-mini")
        fallback = openai.LLM(
            model="nvidia/llama-3.3-nemotron-super-49b-v1",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_api_key,
        )
    else:
        primary = openai.LLM(
            model="nvidia/llama-3.3-nemotron-super-49b-v1",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_api_key,
        )
        fallback = openai.LLM(model="gpt-4o-mini")

    return FallbackAdapter(
        llm=[primary, fallback],
        attempt_timeout=10.0,
        max_retry_per_llm=1,
    )

def get_tts():
    return openai.TTS(voice="nova")

# ---------------------------------------------------------------------------
# Telemetry: persist every metric event to telemetry/<run_id>.jsonl
# ---------------------------------------------------------------------------
TELEMETRY_DIR = Path(__file__).parent / "telemetry"
TELEMETRY_DIR.mkdir(exist_ok=True)

def _new_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{AGENT_PROVIDER}_{ts}"

RUN_ID = _new_run_id()

def _telemetry_path() -> Path:
    return TELEMETRY_DIR / f"{RUN_ID}.jsonl"

def log_metric_to_file(metric_type: str, data: dict):
    record = {
        "run_id": RUN_ID,
        "provider": AGENT_PROVIDER,
        "metric_type": metric_type,
        "timestamp": time.time(),
        "iso_time": datetime.now(timezone.utc).isoformat(),
        **data,
    }
    with open(_telemetry_path(), "a") as f:
        f.write(json.dumps(record) + "\n")

class CollectConsent(AgentTask[bool]):
    def __init__(self, chat_ctx) -> None:
        super().__init__(
            instructions="""
            You are Sally from Lowe's Home Improvement.
            Ask if you may record the call for quality purposes. Get a clear yes or no.
            Keep it to one short sentence. Do not over-explain.
            NEVER output stage directions, tone markers, asterisks, or meta-commentary.
            Only output the exact words to be spoken aloud. No brackets, no parentheses, no descriptions of how to speak.
            """ ,
            chat_ctx=chat_ctx,
        )
    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions="""
            Say: Hi, this is Sally from Lowe's. Do you mind if I record this call for quality purposes?
            """
        )

    @function_tool()
    async def consent_given(self) -> None:
        """Use this when the user gives consent to record the call."""
        self.complete(True)
        
    @function_tool()
    async def consent_declined(self) -> None:
        """Use this when the user does not give consent to record the call."""
        self.complete(False)

class ManagerAgent(Agent):
    def __init__(self, chat_ctx=None):
        super().__init__(
            instructions="""
                You are a customer service manager at Lowe's Home Improvement.
                Handle escalations. Be solution-focused and empathetic.
                You can offer refunds up to $250, credits, or other accommodations.
                Keep responses under 2 sentences. Be direct.
                NEVER output stage directions, tone markers, asterisks, or meta-commentary.
                Only output the exact words to be spoken aloud.
            """,
            chat_ctx=chat_ctx,
            tts=get_tts(),
        )
    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions="""
            Acknowledge the customer's issue in one sentence and ask how you can help resolve it.
            """
        )
        

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are Sally, a professional customer service agent at Lowe's Home Improvement.
                Keep responses concise — 1 to 2 sentences max. Be direct and helpful.
                Do not use filler words, announcements, or overly friendly language.
                Help with general queries. If they ask for a manager or you cannot resolve their issue,
                transfer them using the escalate_to_manager tool.
                NEVER output stage directions, tone markers, asterisks, or meta-commentary like *warmly* or (in a friendly tone).
                Only output the exact words to be spoken aloud. No formatting, no markdown, no annotations.
                """
                )


    @function_tool()
    async def escalate_to_manager(self, context: RunContext) -> ManagerAgent:
        """Transfer the Customer call to a manager when requested or when you cannot resolve their issue."""
        return ManagerAgent(chat_ctx=self.chat_ctx), "Transfering to a Manager now."
    
    
    async def on_enter(self) -> None:
        consent = await CollectConsent(chat_ctx=self.chat_ctx)

        if consent:
            await self.session.generate_reply(
                instructions="Say: Thanks. How can I help you today?"
            )
        else:
            await self.session.generate_reply(
                instructions="Say: No problem, I won't record. How can I help you?"
            )
    

    #await context.session.end()
    
    # @function_tool()
    # async def lookup_weather(
    #         self,
    #         context: RunContext,
    #         location: str,
    #     ) -> dict:
    #     """Lookup weather for a given location.

    #     Args:
    #         location: City Name or location to lookup the weather for.
    #     """
    #     await context.session.say("Looking up the weather for you...")
    #     async with httpx.AsyncClient() as client:
    #         geo_response = await client.get(
    #             "https://geocoding-api.open-meteo.com/v1/search", 
    #             params={"name": location, "count": 1},
    #         )
    #         geo_data= geo_response.json()

    #         if not geo_data.get("results"):
    #             raise ToolError(f"Location not found: {location}")

    #         lat = geo_data["results"][0]["latitude"]
    #         lon = geo_data["results"][0]["longitude"]
    #         place_name = geo_data["results"][0]["name"]
            
    #         weather_response = await client.get(
    #             "https://api.open-meteo.com/v1/forecast", 
    #             params={
    #                 "latitude": lat, 
    #                 "longitude": lon, 
    #                 "current": "temperature_2m,weather_code",
    #                 "temperature_unit": "fahrenheit",
    #             },
    #         )
    #         weather = weather_response.json()
    #         return {
    #             "location": place_name, 
    #             "temperature": weather["current"]["temperature_2m"],
    #             "weather_code": weather["current"]["weather_code"]
    #         }
server = AgentServer()

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    logger.info(f"Starting agent with provider: {AGENT_PROVIDER} | run_id: {RUN_ID}")
    stt_engine = None if MUTE_MIC else get_stt()
    if MUTE_MIC:
        logger.info("Mic MUTED (MUTE_MIC=1) — STT disabled, audio input will be ignored")

    session = AgentSession(
        stt=stt_engine,
        llm=get_llm(),
        tts=get_tts(),
        vad=vad,
        turn_detection=MultilingualModel(),
        preemptive_generation=True,
        mcp_servers=[
            mcp.MCPServerHTTP(url="https://docs.livekit.io/mcp/"),
        ]
    )

    usage_collector = metrics.UsageCollector() 
    last_eou_metrics: metrics.EOUMetrics | None = None
    session_start_time = time.time()
    turn_count = 0
    interruption_count = 0
    agent_is_speaking = False
    last_user_eou_time: float | None = None  # when user stopped speaking
    stt_transcripts: list[dict] = []  # {text, is_final, timestamp}

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        nonlocal last_eou_metrics
        m = ev.metrics

        if m.type == "eou_metrics":
            last_eou_metrics = m
            log_metric_to_file("eou", {
                "end_of_utterance_delay": m.end_of_utterance_delay,
                "transcription_delay": m.transcription_delay,
            })
        elif m.type == "llm_metrics":
            log_metric_to_file("llm", {
                "model": getattr(m, "model_name", ""),
                "ttft": m.ttft,
                "prompt_tokens": m.prompt_tokens,
                "completion_tokens": m.completion_tokens,
                "tokens_per_second": m.tokens_per_second,
            })
        elif m.type == "tts_metrics":
            log_metric_to_file("tts", {
                "ttfb": m.ttfb,
                "audio_duration": m.audio_duration,
            })
        elif m.type == "stt_metrics":
            log_metric_to_file("stt", {
                "audio_duration": getattr(m, "audio_duration", 0),
            })

        metrics.log_metrics(m)
        usage_collector.collect(m)

    # ── STT transcript capture (for WER) ──
    @session.on("user_input_transcribed")
    def _on_user_transcribed(ev: UserInputTranscribedEvent):
        if ev.is_final and ev.transcript.strip():
            stt_transcripts.append({
                "text": ev.transcript.strip(),
                "timestamp": ev.created_at,
                "language": str(ev.language) if ev.language else None,
            })
            log_metric_to_file("stt_transcript", {
                "transcript": ev.transcript.strip(),
                "is_final": True,
            })

    # ── Agent response text capture (for live transcript) ──
    last_agent_transcript_id: str | None = None  # track last logged assistant msg id

    @session.on("conversation_item_added")
    def _on_conversation_item(ev: ConversationItemAddedEvent):
        nonlocal last_agent_transcript_id
        try:
            item = ev.item
            if getattr(item, 'role', None) == 'assistant':
                text = getattr(item, 'text_content', None)
                msg_id = getattr(item, 'id', None)
                if text and text.strip() and msg_id != last_agent_transcript_id:
                    last_agent_transcript_id = msg_id
                    log_metric_to_file("agent_transcript", {
                        "transcript": text.strip(),
                    })
        except Exception:
            pass

    def _capture_latest_agent_text():
        """Capture agent text from session history when agent stops speaking."""
        nonlocal last_agent_transcript_id
        try:
            msgs = list(session.history.messages)
            for msg in reversed(msgs):
                if getattr(msg, 'role', None) == 'assistant':
                    text = getattr(msg, 'text_content', None)
                    msg_id = getattr(msg, 'id', None)
                    if text and text.strip() and msg_id != last_agent_transcript_id:
                        last_agent_transcript_id = msg_id
                        log_metric_to_file("agent_transcript", {
                            "transcript": text.strip(),
                        })
                    break
        except Exception:
            pass

    # ── Interruption & turn tracking ──
    @session.on("user_state_changed")
    def _on_user_state_changed(ev: UserStateChangedEvent):
        nonlocal interruption_count, last_user_eou_time
        if ev.new_state == "speaking" and agent_is_speaking:
            interruption_count += 1
            log_metric_to_file("interruption", {
                "interruption_count": interruption_count,
            })
        if ev.old_state == "speaking" and ev.new_state != "speaking":
            last_user_eou_time = ev.created_at

    @session.on("agent_state_changed")
    def on_agent_state_changed(ev: AgentStateChangedEvent):
        nonlocal agent_is_speaking, turn_count, last_user_eou_time

        if ev.new_state == "speaking":
            agent_is_speaking = True
            turn_count += 1
            # TTFA
            if last_eou_metrics:
                elapsed = time.time() - last_eou_metrics.timestamp
                logger.info(f"TTFA: {elapsed:.3f}s")
                log_metric_to_file("ttfa", {"ttfa": elapsed})
            # Turn round-trip: user EOU → agent starts speaking
            if last_user_eou_time is not None:
                turn_rtt = time.time() - last_user_eou_time
                log_metric_to_file("turn_rtt", {
                    "turn_rtt": round(turn_rtt, 4),
                    "turn_number": turn_count,
                })
                last_user_eou_time = None
        else:
            if agent_is_speaking:
                # Agent just stopped speaking — capture the response text
                _capture_latest_agent_text()
            agent_is_speaking = False

    async def log_usage():
        summary = usage_collector.get_summary()
        session_duration = time.time() - session_start_time
        logger.info("Usage summary: %s", summary)
        log_metric_to_file("usage_summary", {
            "llm_prompt_tokens": summary.llm_prompt_tokens,
            "llm_completion_tokens": summary.llm_completion_tokens,
            "tts_characters_count": summary.tts_characters_count,
            "session_duration": round(session_duration, 2),
            "turn_count": turn_count,
            "interruption_count": interruption_count,
            "stt_transcript_count": len(stt_transcripts),
        })

    ctx.add_shutdown_callback(log_usage)
    
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        ),
    )
    await ctx.connect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--provider", choices=["nemo", "deep"], default=None)
    known, remaining = parser.parse_known_args()
    if known.provider:
        AGENT_PROVIDER = known.provider
        RUN_ID = _new_run_id()
        logger.info(f"Provider set via CLI: {AGENT_PROVIDER}")
    # Pass remaining args to LiveKit CLI
    import sys
    sys.argv = [sys.argv[0]] + remaining
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))


