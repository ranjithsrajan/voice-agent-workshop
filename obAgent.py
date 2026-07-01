from __future__ import annotations

import asyncio
import logging
from dotenv import load_dotenv
import json
import os
import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()   
from typing import Any
from livekit import rtc, api
from livekit.agents import (
    AgentSession,
    Agent,
    JobContext,
    function_tool,
    RunContext,
    get_job_context,
    cli,
    WorkerOptions,
)
from livekit.agents.voice.room_io import RoomOptions, AudioInputOptions
from livekit.plugins import (
    deepgram,
    openai,
    cartesia,
    silero,
    noise_cancellation,  # noqa: F401
)
from livekit.plugins.turn_detector.english import EnglishModel


# load environment variables, this is optional, only used for local development
load_dotenv(".env.local")
logger = logging.getLogger("outbound-caller")
logger.setLevel(logging.INFO)
outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
class OutboundCaller(Agent):
    def __init__(
        self,
        *,
        name: str,
        delivery_time: str,
        dial_info: dict[str, Any],
    ):
        super().__init__(
            instructions=f"""
            You are a delivery scheduling assistant for a Lowes Home improvement Professional Delivery. Your interface with user will be voice.
            You will be on a call with a Professional who has an upcoming Delivery. Your goal is to confirm the Delivery details.
            As a customer service representative, you will be polite and professional at all times. Allow user to end the conversation.

            When the user would like to be transferred to a human agent, first confirm with them. upon confirmation, use the transfer_call tool.
            The customer's name is {name}. His Delivery is on {delivery_time}.
            """
        )
        # keep reference to the participant for transfers
        self.participant: rtc.RemoteParticipant | None = None
        self.dial_info = dial_info

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions="Greet the Pro Customer by name, introduce yourself as a scheduling assistant from the PRO Delivery, and let them know you're calling about their upcoming Delivery."
        )

    def set_participant(self, participant: rtc.RemoteParticipant):
        self.participant = participant

    async def hangup(self):
        """Helper function to hang up the call by deleting the room"""

        job_ctx = get_job_context()
        await job_ctx.api.room.delete_room(
            api.DeleteRoomRequest(
                room=job_ctx.room.name,
            )
        )

    @function_tool()
    async def transfer_call(self, ctx: RunContext):
        """Transfer the call to a human agent, called after confirming with the user"""

        transfer_to = self.dial_info["transfer_to"]
        if not transfer_to:
            return "cannot transfer call"

        logger.info(f"transferring call to {transfer_to}")

        job_ctx = get_job_context()
        try:
            # Dial the human agent into the same room instead of SIP REFER
            await job_ctx.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    room_name=job_ctx.room.name,
                    sip_trunk_id=outbound_trunk_id,
                    sip_call_to=transfer_to,
                    participant_identity=f"agent-{transfer_to}",
                    wait_until_answered=True,
                )
            )

            logger.info(f"human agent {transfer_to} joined the room")
        except Exception as e:
            logger.error(f"error connecting human agent: {e}")
            return "there was an error connecting the human agent"

        return "human agent has been connected to the call"

    @function_tool()
    async def end_call(self, ctx: RunContext):
        """Called when the user wants to end the call"""
        logger.info(f"ending the call for {self.participant.identity}")

        # let the agent finish speaking before hanging up
        await ctx.wait_for_playout()
        await self.hangup()

    @function_tool()
    async def look_up_availability(
        self,
        ctx: RunContext,
        date: str,
    ):
        """Called when the user asks about alternative delivery time availability

        Args:
            date: The date of the delivery to check availability for
        """
        logger.info(
            f"looking up availability for {self.participant.identity} on {date}"
        )
        await asyncio.sleep(3)
        return {
            "available_times": ["1pm", "2pm", "3pm"],
        }

    @function_tool()
    async def confirm_appointment(
        self,
        ctx: RunContext,
        date: str,
        time: str,
    ):
        """Called when the user confirms their delivery on a specific date.
        Use this tool only when they are certain about the date and time.

        Args:
            date: The date of the delivery
            time: The time of the delivery
        """
        logger.info(
            f"confirming delivery for {self.participant.identity} on {date} at {time}"
        )
        return "delivery confirmed"

    @function_tool()
    async def detected_answering_machine(self, ctx: RunContext):
        """Called when the call reaches voicemail. Use this tool AFTER you hear the voicemail greeting"""
        logger.info(f"detected answering machine for {self.participant.identity}")
        await self.hangup()


async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")

    # Skip direct call rooms — those are handled by the human associate directly
    # Check room name prefix first (most reliable, set before agent dispatch)
    if ctx.room.name.startswith("direct-"):
        logger.info(f"[{ctx.room.name}] direct call room detected (name prefix), agent exiting")
        ctx.shutdown()
        return

    await ctx.connect()

    # Also check room metadata as backup
    try:
        room_meta = json.loads(ctx.room.metadata) if ctx.room.metadata else {}
        if room_meta.get("direct_call"):
            logger.info(f"[{ctx.room.name}] direct call room detected (metadata), agent exiting")
            ctx.shutdown()
            return
    except (json.JSONDecodeError, TypeError):
        pass

    # when dispatching the agent, we'll pass it the approriate info to dial the user
    # dial_info is a dict with the following keys:
    # - phone_number: the phone number to dial
    # - transfer_to: the phone number to transfer the call to when requested
    dial_info = json.loads(ctx.job.metadata)
    participant_identity = phone_number = dial_info["phone_number"]

    # look up the user's phone number and Delivery details
    agent = OutboundCaller(
        name="Ranjith",
        delivery_time="next Tuesday at 3pm",
        dial_info=dial_info,
    )

    # the following uses GPT-4o, Deepgram and Cartesia
    session = AgentSession(
        turn_detection=EnglishModel(),
        vad=silero.VAD.load(),
        stt=deepgram.STT(),
        tts=openai.TTS(),
        llm=openai.LLM(model="gpt-4.1-mini"),
        # you can also use a speech-to-speech model like OpenAI's Realtime API
        # llm=openai.realtime.RealtimeModel()
    )

    # `create_sip_participant` starts dialing the user
    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=outbound_trunk_id,
                sip_call_to=phone_number,
                participant_identity=participant_identity,
                # function blocks until user answers the call, or if the call fails
                wait_until_answered=True,
            )
        )

        # wait for participant to join before starting the session
        participant = await ctx.wait_for_participant(identity=participant_identity)
        logger.info(f"participant joined: {participant.identity}")
        agent.set_participant(participant)

        # Publish user STT transcription to the room so external listeners can see it
        _user_seg_counter = [0]

        @session.on("user_input_transcribed")
        def on_user_transcribed(event):
            if not event.is_final:
                return  # skip interim — only publish final to avoid duplicates

            async def _publish():
                try:
                    _user_seg_counter[0] += 1
                    seg_id = f"user_seg_{_user_seg_counter[0]}"
                    attrs = {
                        "lk.transcription_final": "true",
                        "lk.segment_id": seg_id,
                    }
                    writer = await ctx.room.local_participant.stream_text(
                        topic="lk.transcription",
                        sender_identity=participant_identity,
                        attributes=attrs,
                    )
                    await writer.write(event.transcript)
                    await writer.aclose()
                    logger.info(f"published user transcript: '{event.transcript}'")
                except Exception as e:
                    logger.error(f"error publishing user transcription: {e}")

            asyncio.ensure_future(_publish())

        # now start the session — on_enter greeting will be heard by the callee
        await session.start(
            agent=agent,
            room=ctx.room,
            room_options=RoomOptions(
                audio_input=AudioInputOptions(
                    noise_cancellation=noise_cancellation.BVCTelephony(),
                ),
                participant_identity=participant_identity,
                close_on_disconnect=False,
            ),
        )

    except api.TwirpError as e:
        logger.error(
            f"error creating SIP participant: {e.message}, "
            f"SIP status: {e.metadata.get('sip_status_code')} "
            f"{e.metadata.get('sip_status')}"
        )
        ctx.shutdown()
        
async def request_fnc(req):
    """Reject jobs for direct call rooms so the agent never joins them."""
    try:
        room_name = req.room.name if req.room else ""
        room_meta = req.room.metadata if req.room else ""
        logger.info(f"[request_fnc] job received for room='{room_name}', agent='{req.agent_name}', meta='{room_meta}'")

        # Reject if room name starts with "direct-"
        if room_name.startswith("direct-"):
            logger.info(f"[request_fnc] REJECTING job for direct call room: {room_name}")
            await req.reject()
            return

        # Reject if room metadata marks it as a direct call
        try:
            meta = json.loads(room_meta) if room_meta else {}
            if meta.get("direct_call"):
                logger.info(f"[request_fnc] REJECTING job for direct call room (metadata): {room_name}")
                await req.reject()
                return
        except (json.JSONDecodeError, TypeError):
            pass

        logger.info(f"[request_fnc] ACCEPTING job for room: {room_name}")
        await req.accept()
    except Exception as e:
        logger.error(f"[request_fnc] ERROR: {e}", exc_info=True)
        await req.reject()


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            request_fnc=request_fnc,
            agent_name="outbound-caller",
        )
    )