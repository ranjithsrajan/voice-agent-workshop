from asyncio import Server
import logging
import os
import certifi
import time
import httpx

os.environ["SSL_CERT_FILE"] = certifi.where()

from dotenv import load_dotenv
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents import llm,stt,tts, room_io
from livekit.agents import AgentStateChangedEvent, MetricsCollectedEvent, metrics
from livekit.agents import function_tool, RunContext, ToolError
from livekit.agents import mcp
from livekit.agents import AgentTask
from livekit import api

logger = logging.getLogger("_name_")

from livekit.agents import (
    Agent,
    AgentSession,
    AgentServer,
    JobContext,
    RoomInputOptions,
    WorkerOptions,
    cli,
)
from livekit.plugins import deepgram, noise_cancellation, openai, silero, cartesia

logger = logging.getLogger("agent")
vad = silero.VAD.load()

load_dotenv(".env.local")

outbound_trunk_id = os.getenv("OUTBOUND_TRUNK_ID")

class CollectConsent(AgentTask[bool]):
    def __init__(self, chat_ctx) -> None:
        super().__init__(
            instructions="""
            Briefly introduce yourself as Sally & Lowe's Home Improvement and 
            Ask for recording consent and get clear yes or no answer.
            Be polite and professional.
            """ ,
            chat_ctx=chat_ctx,
        )
    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions="""
            Briefly introduce yourself & Lowe's Home Improvement, then ask for permission to record the call for quality improvement purposes.
            Explain that the recording will be used to improve the service.
            and make it clear that the caller can decline if they prefer.
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
                You are a customer Service manager agent for Lowe's Home Improvement.
                You Handle escalations that your agents couldnt resolve. Be Empathetic helpful and solution focused
                You have authority to offer refunds up to $250 and credits or other accommodations
                You can also answer questions about Lowe's Home Improvement.
            """,
            chat_ctx=chat_ctx,
            tts=openai.TTS(),
        )
    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions="""
            Briefly introduce yourself as a manager at Lowe's Home Improvement, 
            Acknowledge their issue and offer to help resolve it.
            """
        )
        

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a friendly customer service agent for Lowe's Home Improvement.
                Help with genral quires. If they ask for a manager or you cannot resolve their issue, 
                transfer them to the manager by using the escalate_to_manager tool.
                """

                # "You are an upbeat, slightly sarcastic voice AI for tech support."
                # "Help the caller fix issues without rambling, and keep replies under 3 sentences."
                # "You can also look up the weather if asked"
                # "You can also answer qustions about livekit features and capabilities, API references, and documentation. or how to build something with livekit"
                # "If you are asked about something outside your scope, say you don't know"
                # "use the docs search tools to accuratley answer questions about livekit"
                )


    @function_tool()
    async def escalate_to_manager(self, context: RunContext) -> ManagerAgent:
        """Transfer the Customer call to a manager when requested or when you cannot resolve their issue."""
        return ManagerAgent(chat_ctx=self.chat_ctx), "Transfering to a Manager now."
    
    
    async def on_enter(self) -> None:
        consent = await CollectConsent(chat_ctx=self.chat_ctx)

        if consent:
            await self.session.generate_reply(
                instructions="Thank you for your consent. How can I help you today?"
            )
            #await self.session.end()
        else:
            await self.session.generate_reply(
                instructions="Let them know that yuo will not record the call and proceed with the conversation."
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
    session = AgentSession(
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4.1-mini"),
        tts=openai.TTS(),
        vad=vad,
        turn_detection=MultilingualModel(),
        preemptive_generation=True,
        mcp_servers=[
            mcp.MCPServerHTTP(url="https://docs.livekit.io/mcp/"),
        ]
    )

    usage_collector = metrics.UsageCollector() 
    last_eou_metrics: metrics.EOUMetrics | None = None
    
    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        nonlocal last_eou_metrics
        if ev.metrics.type == "eou_metrics":
            last_eou_metrics = ev.metrics

        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)
        
    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info("Usage summary: %s", summary)

    ctx.add_shutdown_callback(log_usage)

    @session.on("agent_state_changed")
    def on_agent_state_changed(ev: AgentStateChangedEvent):
        if ev.new_state == "speaking":
            if last_eou_metrics:
                elapsed = time.time() - last_eou_metrics.timestamp
                logger.info(f"TTFA: {elapsed:.3f}s")
    
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
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))


