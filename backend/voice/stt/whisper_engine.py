# ============================================================
# ActOS — Speech-to-Text Engine
# Tech Stack: OpenAI Whisper Large V3 + Deepgram (streaming)
# Supports: Tamil, Tanglish, English, Hindi, Telugu, Malayalam
# ============================================================

import openai
import tempfile
import os
from pathlib import Path
from loguru import logger
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class TranscriptionResult:
    text: str                    # Transcribed text
    language: str                # Detected language code
    confidence: float            # 0.0 - 1.0
    is_mixed: bool               # True if Tanglish/code-switching
    duration_seconds: float


class WhisperSTT:
    """
    Whisper Large V3 Speech-to-Text
    Handles Tamil, Tanglish, English, Hindi, Telugu, Malayalam
    """

    # Language hints for Whisper — improves accuracy for Indian languages
    LANGUAGE_HINTS = {
        "tamil":   "ta",
        "hindi":   "hi",
        "telugu":  "te",
        "malayalam": "ml",
        "english": "en",
        "tanglish": None,  # No hint — let Whisper detect mixed
    }

    # Whisper prompt to improve Tamil/Tanglish accuracy
    TAMIL_PROMPT = (
        "The following is a voice command in Tamil, Tanglish (Tamil+English mix), "
        "or English. Common words: podu, pannu, open panni, search pannu, "
        "WhatsApp la, message podu, call podu, anna, dei, amma."
    )

    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("✅ Whisper STT engine initialized")

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        audio_format: str = "webm",
        language_hint: str = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio bytes to text using Whisper Large V3
        
        Args:
            audio_bytes: Raw audio data from browser WebRTC/MediaRecorder
            audio_format: webm, mp3, wav, ogg, m4a
            language_hint: Optional language code (ta, en, hi)
        
        Returns:
            TranscriptionResult with text, language, confidence
        """
        # Save to temp file (Whisper needs file input)
        with tempfile.NamedTemporaryFile(
            suffix=f".{audio_format}", delete=False
        ) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as audio_file:
                response = await self.client.audio.transcriptions.create(
                    model="whisper-1",           # OpenAI Whisper Large V3
                    file=audio_file,
                    response_format="verbose_json",
                    language=language_hint,      # None = auto-detect
                    prompt=self.TAMIL_PROMPT,    # Improves Tamil/Tanglish accuracy
                    temperature=0.0,             # Deterministic output
                )

            text = response.text.strip()
            detected_lang = getattr(response, "language", "en") or "en"
            duration = getattr(response, "duration", 0.0) or 0.0

            # Detect if it's mixed/Tanglish
            is_mixed = self._detect_mixed_language(text)

            logger.info(
                f"🎙 Transcribed: '{text[:80]}...' | "
                f"Lang: {detected_lang} | Mixed: {is_mixed}"
            )

            return TranscriptionResult(
                text=text,
                language=detected_lang,
                confidence=0.95,   # Whisper doesn't return confidence directly
                is_mixed=is_mixed,
                duration_seconds=duration,
            )

        except Exception as e:
            logger.error(f"❌ Whisper transcription failed: {e}")
            raise
        finally:
            os.unlink(tmp_path)

    def _detect_mixed_language(self, text: str) -> bool:
        """
        Detect if text is Tanglish (Tamil+English mix)
        Checks for Tamil romanization patterns alongside English
        """
        tamil_patterns = [
            "podu", "pannu", "panni", "paar", "sollu", "vaa", "po",
            "dei", "da", "di", "anna", "amma", "appa", "la", "ku",
            "nu", "oru", "enna", "enga", "yenna", "paaru", "kelu",
            "open panni", "search pannu", "message podu", "call podu",
        ]
        text_lower = text.lower()
        tamil_count = sum(1 for p in tamil_patterns if p in text_lower)
        has_english = any(c.isascii() and c.isalpha() for c in text)
        return tamil_count >= 2 and has_english


class DeepgramStreamingSTT:
    """
    Deepgram Streaming STT for realtime voice conversations
    Lower latency than Whisper — used for continuous listening mode
    """

    def __init__(self):
        from deepgram import DeepgramClient
        self.client = DeepgramClient(settings.DEEPGRAM_API_KEY)
        logger.info("✅ Deepgram streaming STT initialized")

    async def stream_transcribe(self, audio_stream, callback):
        """
        Stream audio chunks and call callback with partial transcripts
        Used for: wake word detection, realtime conversation
        """
        from deepgram import LiveTranscriptionEvents, LiveOptions

        options = LiveOptions(
            model="nova-2",
            language="en-IN",          # Indian English variant
            smart_format=True,
            interim_results=True,       # Get partial results fast
            utterance_end_ms=1000,
            vad_events=True,            # Voice activity detection
        )

        connection = self.client.listen.live.v("1")

        connection.on(LiveTranscriptionEvents.Transcript, callback)

        await connection.start(options)

        async for chunk in audio_stream:
            connection.send(chunk)

        await connection.finish()


# ── Singleton instances ──
whisper_stt = WhisperSTT()
deepgram_stt = DeepgramStreamingSTT()
