import os
import re
import json
import subprocess
import time
import asyncio
import logging
import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from livekit import rtc, api

load_dotenv("../.env.local")

logger = logging.getLogger("ops-server")
logging.basicConfig(level=logging.INFO)

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

active_calls: dict = {}


class CallRequest(BaseModel):
    phone_number: str
    transfer_to: str = ""
    caller_name: str = ""


def _generate_listener_token(room_name: str, identity: str) -> str:
    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name("OpsUI Listener")
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_subscribe=True,
            can_publish=False,
        ))
    )
    return token.to_jwt()


@app.post("/api/call")
async def initiate_call(req: CallRequest):
    metadata = json.dumps({
        "phone_number": req.phone_number,
        "transfer_to": req.transfer_to,
    })

    env = os.environ.copy()

    cmd = [
        "lk", "dispatch", "create",
        "--new-room",
        "--agent-name", "outbound-caller",
        "--metadata", metadata,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr.strip())

        output = result.stdout.strip()
        dispatch_id = ""
        room_name = ""
        match_id = re.search(r'id:"([^"]+)"', output)
        match_room = re.search(r'room:"([^"]+)"', output)
        if match_id:
            dispatch_id = match_id.group(1)
        if match_room:
            room_name = match_room.group(1)

        call_id = dispatch_id or f"call-{int(time.time())}"
        active_calls[call_id] = {
            "call_id": call_id,
            "dispatch_id": dispatch_id,
            "room_name": room_name,
            "phone_number": req.phone_number,
            "caller_name": req.caller_name,
            "status": "ringing",
            "started_at": time.time(),
            "transcripts": [],
        }

        return {
            "status": "ok",
            "call_id": call_id,
            "dispatch_id": dispatch_id,
            "room_name": room_name,
            "output": output,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="lk command timed out")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="lk CLI not found in PATH")


@app.get("/api/call/{call_id}")
async def get_call_status(call_id: str):
    call = active_calls.get(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    elapsed = time.time() - call["started_at"]
    if call["status"] == "ringing" and elapsed > 5:
        call["status"] = "connected"
    if call["status"] == "connected" and elapsed > 300:
        call["status"] = "ended"

    return {
        "call_id": call["call_id"],
        "status": call["status"],
        "room_name": call["room_name"],
        "phone_number": call["phone_number"],
        "caller_name": call["caller_name"],
        "started_at": call["started_at"],
    }


@app.get("/api/call/{call_id}/transcript")
async def stream_transcript(call_id: str):
    """SSE endpoint: joins the LiveKit room and streams transcription events in real time."""
    call = active_calls.get(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    room_name = call.get("room_name", "")
    if not room_name:
        raise HTTPException(status_code=400, detail="No room associated with call")

    TOPIC_TRANSCRIPTION = "lk.transcription"
    ATTR_FINAL = "lk.transcription_final"
    ATTR_SEGMENT_ID = "lk.segment_id"

    async def event_generator():
        room = rtc.Room()
        connected = False
        background_tasks = []

        transcript_queue: asyncio.Queue = asyncio.Queue()

        def _identity_to_speaker(identity: str) -> str:
            if not identity or identity == "ops-listener":
                return "Agent"
            if identity.startswith("+") or identity.replace("-", "").isdigit():
                return "Customer"
            return "Agent"

        # Text stream handler for topic "lk.transcription" (new LiveKit agents SDK)
        def on_text_stream(reader, participant_identity: str):
            logger.info(f"[text-stream] RECEIVED stream from '{participant_identity}', "
                        f"stream_id={reader.info.stream_id}, attrs={reader.info.attributes}")
            attrs = reader.info.attributes or {}
            is_final = attrs.get(ATTR_FINAL, "false") == "true"
            segment_id = attrs.get(ATTR_SEGMENT_ID, reader.info.stream_id)

            # sender_identity from header tells us who the transcription is for
            speaker = _identity_to_speaker(participant_identity)
            logger.info(f"[text-stream] speaker={speaker}, is_final={is_final}, seg={segment_id}")

            async def _read_stream():
                try:
                    collected = ""
                    async for chunk in reader:
                        collected += chunk
                        # Only stream chunk-by-chunk for interim transcripts
                        if not is_final:
                            transcript_queue.put_nowait({
                                "event": "transcription",
                                "speaker": speaker,
                                "text": collected,
                                "is_final": False,
                                "segment_id": segment_id,
                                "time": time.strftime("%M:%S"),
                            })

                    # Emit final once when stream closes
                    if collected.strip():
                        logger.info(f"[text-stream] {speaker}: '{collected}' (final={is_final})")
                        transcript_queue.put_nowait({
                            "event": "transcription",
                            "speaker": speaker,
                            "text": collected,
                            "is_final": True,
                            "segment_id": segment_id,
                            "time": time.strftime("%M:%S"),
                        })
                except Exception as e:
                    logger.error(f"[text-stream] error reading stream: {e}")

            task = asyncio.get_event_loop().create_task(_read_stream())
            background_tasks.append(task)

        # Register text stream handler BEFORE connecting
        room.register_text_stream_handler(TOPIC_TRANSCRIPTION, on_text_stream)

        @room.on("participant_connected")
        def on_participant_connected(participant):
            logger.info(f"[room] participant connected: {participant.identity}")
            transcript_queue.put_nowait({
                "event": "participant_connected",
                "identity": participant.identity,
            })

        @room.on("participant_disconnected")
        def on_participant_disconnected(participant):
            logger.info(f"[room] participant disconnected: {participant.identity}")
            transcript_queue.put_nowait({
                "event": "participant_disconnected",
                "identity": participant.identity,
            })

        try:
            token = _generate_listener_token(room_name, "ops-listener")
            logger.info(f"[transcript-listener] connecting to room {room_name}")
            await room.connect(LIVEKIT_URL, token)
            connected = True
            logger.info(f"[transcript-listener] connected to room {room_name}, "
                        f"participants: {list(room.remote_participants.keys())}")

            yield f"data: {json.dumps({'event': 'connected', 'room': room_name})}\n\n"

            while True:
                try:
                    entry = await asyncio.wait_for(transcript_queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(entry)}\n\n"

                    # Store final transcripts for disposition file
                    if entry.get("event") == "transcription" and entry.get("is_final"):
                        call.setdefault("transcripts", []).append({
                            "speaker": entry.get("speaker"),
                            "text": entry.get("text"),
                            "time": entry.get("time"),
                        })

                    if entry.get("event") == "participant_disconnected":
                        remaining = room.remote_participants
                        if len(remaining) <= 1:
                            call["status"] = "ended"
                            yield f"data: {json.dumps({'event': 'call_ended'})}\n\n"
                            break
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'event': 'heartbeat'})}\n\n"

                    if call.get("status") == "ended":
                        yield f"data: {json.dumps({'event': 'call_ended'})}\n\n"
                        break

        except Exception as e:
            logger.error(f"[transcript-listener] error: {e}", exc_info=True)
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
        finally:
            for task in background_tasks:
                task.cancel()
            if connected:
                await room.disconnect()
                logger.info(f"[transcript-listener] disconnected from room {room_name}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


class SummarizeRequest(BaseModel):
    transcript: list[dict] = []


@app.post("/api/call/{call_id}/summarize")
async def summarize_call(call_id: str, req: SummarizeRequest):
    """Use OpenAI to summarize the call transcript and suggest a disposition."""
    call = active_calls.get(call_id)

    transcript_text = ""
    for entry in req.transcript:
        speaker = entry.get("speaker", "Unknown")
        text = entry.get("text", "")
        transcript_text += f"{speaker}: {text}\n"

    if not transcript_text.strip():
        return {
            "summary": "No transcript available for this call.",
            "suggested_disposition": "No Contact",
            "key_points": [],
        }

    import openai as oai
    client = oai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a call center analyst. Given a call transcript between an AI Agent and a Customer, "
                        "provide:\n"
                        "1. A concise summary (2-3 sentences)\n"
                        "2. Key points as a JSON array of strings\n"
                        "3. A suggested engagement disposition from these options: "
                        "\"Delivery Confirmed\", \"Delivery Rescheduled\", \"Customer Callback Requested\", "
                        "\"Transferred to Human Agent\", \"Voicemail Left\", \"No Contact\", \"Customer Declined\"\n\n"
                        "Respond in JSON format:\n"
                        "{\"summary\": \"...\", \"key_points\": [\"...\"], \"suggested_disposition\": \"...\"}"
                    ),
                },
                {
                    "role": "user",
                    "content": f"Call transcript:\n{transcript_text}",
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        result = json.loads(response.choices[0].message.content)
        return {
            "summary": result.get("summary", ""),
            "key_points": result.get("key_points", []),
            "suggested_disposition": result.get("suggested_disposition", ""),
        }
    except Exception as e:
        logger.error(f"Error summarizing call: {e}")
        return {
            "summary": f"Auto-summary unavailable: {str(e)}",
            "suggested_disposition": "",
            "key_points": [],
        }


class SaveDispositionRequest(BaseModel):
    disposition: str
    notes: str = ""
    summary: str = ""


@app.post("/api/call/{call_id}/disposition")
async def save_disposition(call_id: str, req: SaveDispositionRequest):
    """Save the engagement disposition for the call."""
    call = active_calls.get(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    call["disposition"] = req.disposition
    call["notes"] = req.notes
    call["summary"] = req.summary
    logger.info(f"Saved disposition for {call_id}: {req.disposition}")

    # Save disposition as a raw text file
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dispositions_dir = os.path.join(project_root, "dispositions")
    os.makedirs(dispositions_dir, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{call_id}_{timestamp}.txt"
    filepath = os.path.join(dispositions_dir, filename)

    transcript_lines = []
    for t in call.get("transcripts", []):
        speaker = t.get("speaker", "Unknown")
        text = t.get("text", "")
        transcript_lines.append(f"  {speaker}: {text}")

    content = (
        f"Call ID: {call_id}\n"
        f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Caller: {call.get('caller_name', 'Unknown')}\n"
        f"Phone: {call.get('phone_number', 'Unknown')}\n"
        f"Disposition: {req.disposition}\n"
        f"Notes: {req.notes}\n"
        f"\n--- Summary ---\n{req.summary}\n"
        f"\n--- Transcript ---\n" + ("\n".join(transcript_lines) if transcript_lines else "(no transcript)")
        + "\n"
    )

    with open(filepath, "w") as f:
        f.write(content)
    logger.info(f"Disposition file saved: {filepath}")

    return {"status": "ok", "message": f"Disposition '{req.disposition}' saved", "file": filename}


@app.post("/api/call/{call_id}/end")
async def end_call(call_id: str):
    call = active_calls.get(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    room_name = call.get("room_name", "")
    if room_name:
        env = os.environ.copy()
        try:
            subprocess.run(
                ["lk", "room", "delete", room_name],
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )
        except Exception:
            pass

    call["status"] = "ended"
    return {"status": "ok", "message": "Call ended"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
