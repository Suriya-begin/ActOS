"""
ActOS — WebSocket Route
Blueprint: WebRTC + WebSockets for realtime voice streaming and live updates
ws://localhost:8000/ws/voice   → Stream mic audio, get live transcript + responses
ws://localhost:8000/ws/status  → Push command execution status to dashboard
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.voice.stt.whisper_engine import whisper_engine
from app.voice.tts.elevenlabs_engine import elevenlabs_engine
from app.core.intent_extractor import intent_extractor, ExtractedIntent
from app.core.orchestrator import orchestrator
from loguru import logger
import json
import base64
import asyncio

router = APIRouter()

# Connection manager for broadcasting status updates
active_connections: dict[str, WebSocket] = {}
pending_intents: dict[str, ExtractedIntent] = {}


class ConnectionManager:
    async def connect(self, user_id: str, ws: WebSocket):
        await ws.accept()
        active_connections[user_id] = ws
        logger.info(f"WS connected: {user_id}")

    def disconnect(self, user_id: str):
        active_connections.pop(user_id, None)
        pending_intents.pop(user_id, None)

    async def send(self, user_id: str, data: dict):
        ws = active_connections.get(user_id)
        if ws:
            try:
                await ws.send_text(json.dumps(data))
            except Exception as e:
                logger.error(f"Failed to send to WS user {user_id}: {e}")

    async def broadcast(self, data: dict):
        for user_id, ws in list(active_connections.items()):
            try:
                await ws.send_text(json.dumps(data))
            except Exception as e:
                logger.error(f"Failed to broadcast to WS user {user_id}: {e}")


manager = ConnectionManager()


async def process_and_reply(transcript: str, user_id: str):
    """Pipeline: understanding -> orchestrator (LangGraph) -> voice response."""
    session_id = f"sess_{user_id}"
    try:
        # 1. Extract intent — show live status
        await manager.send(user_id, {"type": "status", "text": "Understanding your command..."})
        intent_obj = await intent_extractor.extract(transcript)
        intent_dict = intent_obj.dict()
        await manager.send(user_id, {"type": "intent", "data": intent_dict})

        # Show what language was detected
        lang_display = {
            "tamil": "🇮🇳 Tamil",
            "tanglish": "🇮🇳 Tanglish",
            "english": "🇬🇧 English",
            "hindi": "🇮🇳 Hindi",
            "telugu": "🇮🇳 Telugu",
            "malayalam": "🇮🇳 Malayalam",
        }.get(intent_obj.language, intent_obj.language or "Auto")
        await manager.send(user_id, {"type": "language", "text": lang_display, "code": intent_obj.language})

        # Check for deactivation command
        if intent_obj.action == "deactivate_assistant":
            lang = intent_obj.language or "english"
            if "tanglish" in lang or "tamil" in lang:
                voice_response = "Sari, assistant mode off pannurom. Bye!"
            elif "hindi" in lang:
                voice_response = "Theek hai, assistant band kar raha hun. Bye!"
            else:
                voice_response = "Turning off assistant mode. Goodbye!"
            await manager.send(user_id, {"type": "deactivate", "text": voice_response})
            try:
                audio_bytes = await elevenlabs_engine.speak(voice_response)
                audio_b64 = base64.b64encode(audio_bytes).decode()
                await manager.send(user_id, {"type": "audio_reply", "data": audio_b64})
            except Exception as tts_err:
                logger.error(f"TTS deactivation reply failed: {tts_err}")
            return

        # Handle unknown/clarification
        if intent_obj.action == "unknown" or intent_obj.clarification_needed:
            clarification = intent_obj.clarification_question or "Sorry, I didn't understand. Could you repeat?"
            await manager.send(user_id, {"type": "result", "text": clarification})
            try:
                audio_bytes = await elevenlabs_engine.speak(clarification)
                audio_b64 = base64.b64encode(audio_bytes).decode()
                await manager.send(user_id, {"type": "audio_reply", "data": audio_b64})
            except Exception as tts_err:
                logger.error(f"TTS clarification failed: {tts_err}")
            return

        # 2. Show action being taken
        action_display = _describe_action(intent_obj)
        await manager.send(user_id, {"type": "step", "text": action_display})

        # 3. Run orchestrator with live step callback
        await manager.send(user_id, {"type": "status", "text": "Executing..."})

        async def step_callback(step_text: str):
            await manager.send(user_id, {"type": "step", "text": step_text})

        orchestration_result = await orchestrator.process_command(
            intent_obj, user_id, session_id, step_callback=step_callback
        )

        voice_response = orchestration_result.get("voice_response", "Done.")
        result_data = orchestration_result.get("result", {})
        detected_lang = orchestration_result.get("language", "english")

        # Check if auth required
        if orchestration_result.get("auth_required"):
            pending_intents[user_id] = intent_obj
            await manager.send(user_id, {
                "type": "confirmation_required",
                "message": voice_response,
                "intent": intent_dict
            })
            # Speak the confirmation request
            try:
                audio_bytes = await elevenlabs_engine.speak(voice_response, language=detected_lang)
                audio_b64 = base64.b64encode(audio_bytes).decode()
                await manager.send(user_id, {"type": "audio_reply", "data": audio_b64})
            except Exception as tts_err:
                logger.error(f"TTS auth request failed: {tts_err}")
            return

        # 4. Send text result
        await manager.send(user_id, {
            "type": "result",
            "text": voice_response,
            "data": result_data,
            "language": detected_lang
        })

        # 5. Generate voice reply
        if voice_response:
            try:
                audio_bytes = await elevenlabs_engine.speak(voice_response, language=detected_lang)
                audio_b64 = base64.b64encode(audio_bytes).decode()
                await manager.send(user_id, {"type": "audio_reply", "data": audio_b64})
            except Exception as tts_err:
                logger.error(f"TTS generation failed: {tts_err}")

    except Exception as e:
        logger.error(f"Error processing command '{transcript}': {e}")
        error_msg = "Sorry, I encountered an error. Please try again."
        await manager.send(user_id, {"type": "error", "message": str(e)})
        await manager.send(user_id, {"type": "result", "text": error_msg})
        try:
            audio_bytes = await elevenlabs_engine.speak(error_msg)
            audio_b64 = base64.b64encode(audio_bytes).decode()
            await manager.send(user_id, {"type": "audio_reply", "data": audio_b64})
        except Exception:
            pass


def _describe_action(intent: ExtractedIntent) -> str:
    """Generate a human-readable description of what ActOS is about to do"""
    action = intent.action
    target = intent.target or ""
    app = intent.app or ""
    content = intent.content or ""

    descriptions = {
        "play_music": f"🎵 Searching YouTube for '{target}'...",
        "search": f"🔍 Searching for '{target or content}'...",
        "search_product": f"🛒 Searching {app.capitalize()} for '{target}'...",
        "open_app": f"🌐 Opening {target or app}...",
        "open_browser": f"🌐 Opening {target or app}...",
        "send_message": f"💬 Composing WhatsApp message to {target}...",
        "make_call": f"📞 Initiating call to {target}...",
        "send_email": f"📧 Composing email to {target}...",
        "set_reminder": f"⏰ Setting reminder: '{target or content}'...",
        "pause": "⏸️ Pausing playback...",
        "play": "▶️ Resuming playback...",
        "skip_ad": "⏭️ Skipping ad...",
        "scroll_down": "⬇️ Scrolling down...",
        "scroll_up": "⬆️ Scrolling up...",
        "click": f"👆 Clicking '{target}'...",
        "go_back": "⬅️ Navigating back...",
        "type_text": f"⌨️ Typing '{content or target}'...",
        "fill_form": f"📝 Filling form...",
        "summarize_page": "📄 Reading and summarizing page...",
        "book_cab": f"🚗 Looking for cabs to {target}...",
        "deactivate_assistant": "👋 Turning off...",
    }
    return descriptions.get(action, f"⚙️ Executing {action} on {app}...")


@router.websocket("/voice/{user_id}")
async def voice_websocket(websocket: WebSocket, user_id: str):
    """
    Realtime voice pipeline over WebSocket.
    """
    await manager.connect(user_id, websocket)
    audio_buffer = bytearray()
    audio_format = "webm"

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "audio_chunk":
                chunk = base64.b64decode(message["data"])
                audio_buffer.extend(chunk)
                audio_format = message.get("format", "webm")

            elif msg_type == "audio_end":
                if audio_buffer:
                    await manager.send(user_id, {"type": "status", "text": "Transcribing..."})
                    try:
                        transcript_result = await whisper_engine.transcribe_bytes(bytes(audio_buffer), format=audio_format)
                        transcript = transcript_result["text"]
                        detected_lang = transcript_result.get("language", "en")
                        audio_buffer.clear()
                        audio_format = "webm"

                        await manager.send(user_id, {
                            "type": "transcript",
                            "text": transcript,
                            "language": detected_lang
                        })

                        # Filter out very short/noisy transcripts before processing
                        # Single words like "um", "uh", "the", "ah" are almost always noise
                        NOISE_WORDS = {"um", "uh", "ah", "mm", "hmm", "eh", "the", "a", "oh", "ok",
                                       ".", ",", "?", "!", "...", "er", "err"}
                        words = transcript.strip().split()
                        is_noise = (
                            len(words) == 0
                            or (len(words) == 1 and words[0].lower() in NOISE_WORDS)
                        )

                        if is_noise:
                            logger.info(f"Transcript '{transcript}' is likely noise — ignoring")
                            await manager.send(user_id, {"type": "status", "text": "idle"})
                        elif user_id in pending_intents:
                            t = transcript.lower()
                            confirm_words = ["yes", "yeah", "yep", "sure", "ok", "proceed", "do it",
                                             "ama", "sari", "ok da", "ha", "haan", "theek hai"]
                            deny_words = ["no", "don't", "stop", "cancel", "illai", "vena",
                                          "nahi", "mat karo", "nope"]

                            if any(word in t for word in confirm_words) and not any(w in t for w in deny_words):
                                intent_obj = pending_intents.pop(user_id)
                                intent_obj.needs_auth = False
                                await manager.send(user_id, {"type": "status", "text": "Confirmed. Executing..."})
                                session_id = f"sess_{user_id}"

                                async def step_cb(step_text: str):
                                    await manager.send(user_id, {"type": "step", "text": step_text})

                                orchestration_result = await orchestrator.process_command(intent_obj, user_id, session_id, step_callback=step_cb)
                                voice_response = orchestration_result.get("voice_response", "Done.")
                                result_data = orchestration_result.get("result", {})
                                lang = orchestration_result.get("language", "english")
                                await manager.send(user_id, {"type": "result", "text": voice_response, "data": result_data, "language": lang})
                                if voice_response:
                                    try:
                                        audio_bytes = await elevenlabs_engine.speak(voice_response, language=lang)
                                        audio_b64 = base64.b64encode(audio_bytes).decode()
                                        await manager.send(user_id, {"type": "audio_reply", "data": audio_b64})
                                    except Exception as tts_err:
                                        logger.error(f"TTS confirmation reply failed: {tts_err}")
                            else:
                                pending_intents.pop(user_id, None)
                                await manager.send(user_id, {"type": "status", "text": "Cancelled"})
                                cancel_msg = "Action cancelled."
                                await manager.send(user_id, {"type": "result", "text": cancel_msg})
                        else:
                            await process_and_reply(transcript, user_id)

                    except Exception as transcribe_err:
                        logger.error(f"Transcription failed: {transcribe_err}")
                        await manager.send(user_id, {"type": "error", "message": "Failed to transcribe audio"})
                else:
                    # Empty buffer (silence)
                    await manager.send(user_id, {"type": "status", "text": "idle"})

            elif msg_type == "text_command":
                text = message.get("text", "").strip()
                if text:
                    await manager.send(user_id, {"type": "transcript", "text": text, "language": "en"})
                    await process_and_reply(text, user_id)

            elif msg_type in ["confirm", "confirm_action"]:
                confirmed = message.get("confirmed", True)
                if confirmed and user_id in pending_intents:
                    intent_obj = pending_intents.pop(user_id)
                    intent_obj.needs_auth = False  # bypass check

                    await manager.send(user_id, {"type": "status", "text": "Confirmed. Executing..."})
                    session_id = f"sess_{user_id}"
                    try:
                        async def step_cb2(step_text: str):
                            await manager.send(user_id, {"type": "step", "text": step_text})

                        orchestration_result = await orchestrator.process_command(intent_obj, user_id, session_id, step_callback=step_cb2)
                        voice_response = orchestration_result.get("voice_response", "Done.")
                        result_data = orchestration_result.get("result", {})
                        lang = orchestration_result.get("language", "english")

                        await manager.send(user_id, {"type": "result", "text": voice_response, "data": result_data, "language": lang})

                        if voice_response:
                            try:
                                audio_bytes = await elevenlabs_engine.speak(voice_response, language=lang)
                                audio_b64 = base64.b64encode(audio_bytes).decode()
                                await manager.send(user_id, {"type": "audio_reply", "data": audio_b64})
                            except Exception as tts_err:
                                logger.error(f"TTS generation failed: {tts_err}")
                    except Exception as exec_err:
                        logger.error(f"Execution failed after confirmation: {exec_err}")
                        await manager.send(user_id, {"type": "error", "message": f"Execution failed: {str(exec_err)}"})
                else:
                    pending_intents.pop(user_id, None)
                    await manager.send(user_id, {"type": "status", "text": "Cancelled"})
                    await manager.send(user_id, {"type": "result", "text": "Action cancelled."})

            elif msg_type == "ping":
                await manager.send(user_id, {"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"WS disconnected: {user_id}")
    except Exception as e:
        logger.error(f"WS unexpected error: {e}")
        manager.disconnect(user_id)


@router.websocket("/status/{user_id}")
async def status_websocket(websocket: WebSocket, user_id: str):
    """Push live dashboard updates to frontend."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        pass
