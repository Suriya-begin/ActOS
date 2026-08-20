"""
ActOS — Voice API Routes
POST /api/voice/transcribe   → Upload audio file, get transcript
POST /api/voice/speak        → Text to speech
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.voice.stt.whisper_engine import whisper_engine
from app.voice.tts.elevenlabs_engine import elevenlabs_engine
from app.security.auth import get_current_user
import io

router = APIRouter()


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = None,
    user: dict = Depends(get_current_user),
):
    """Transcribe uploaded audio file using Whisper Large V3."""
    audio_bytes = await file.read()
    result = await whisper_engine.transcribe_bytes(audio_bytes, language=language)
    return {
        "transcript": result["text"],
        "language":   result["language"],
        "user_id":    user["sub"],
    }


@router.post("/speak")
async def text_to_speech(
    payload: dict,
    user: dict = Depends(get_current_user),
):
    """Convert text to speech audio using ElevenLabs."""
    text = payload.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    audio_bytes = await elevenlabs_engine.speak(text)
    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "attachment; filename=response.mp3"},
    )
