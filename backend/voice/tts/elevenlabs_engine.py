# ============================================================
# ActOS — Text-to-Speech Engine
# Tech Stack: ElevenLabs API
# Converts ActOS responses back to natural voice
# ============================================================

from elevenlabs.client import AsyncElevenLabs
from elevenlabs import VoiceSettings
from loguru import logger
import asyncio

from app.core.config import settings


class ElevenLabsTTS:
    """
    ElevenLabs Text-to-Speech
    Converts ActOS text responses to natural-sounding voice audio
    Streamed back to browser via WebSocket
    """

    def __init__(self):
        self.client = AsyncElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        self.voice_settings = VoiceSettings(
            stability=0.6,
            similarity_boost=0.85,
            style=0.3,
            use_speaker_boost=True,
        )
        logger.info("✅ ElevenLabs TTS engine initialized")

    async def synthesize(self, text: str) -> bytes:
        """
        Convert text to audio bytes (mp3)
        Returns full audio for short responses
        """
        try:
            audio = await self.client.generate(
                text=text,
                voice=self.voice_id,
                model="eleven_multilingual_v2",  # Supports Indian accents
                voice_settings=self.voice_settings,
            )

            audio_bytes = b"".join([chunk async for chunk in audio])
            logger.info(f"🔊 TTS synthesized: '{text[:60]}...' ({len(audio_bytes)} bytes)")
            return audio_bytes

        except Exception as e:
            logger.error(f"❌ ElevenLabs TTS failed: {e}")
            raise

    async def stream_synthesize(self, text: str):
        """
        Stream audio chunks for faster response
        Used for: long responses, real-time conversation
        Yields audio chunks as they're generated
        """
        async for chunk in await self.client.generate(
            text=text,
            voice=self.voice_id,
            model="eleven_multilingual_v2",
            voice_settings=self.voice_settings,
            stream=True,
        ):
            yield chunk

    async def synthesize_confirmation(self, action: str, target: str) -> bytes:
        """
        Pre-built confirmation prompt voice
        Example: "Should I send 'hi' to Ravi on WhatsApp?"
        """
        text = f"Should I {action} to {target}? Say yes to confirm."
        return await self.synthesize(text)

    async def synthesize_success(self, action: str) -> bytes:
        """Success confirmation voice"""
        text = f"Done. {action} completed successfully."
        return await self.synthesize(text)

    async def synthesize_error(self, reason: str) -> bytes:
        """Error voice message"""
        text = f"Sorry, I couldn't complete that. {reason}"
        return await self.synthesize(text)


# ── Singleton ──
elevenlabs_tts = ElevenLabsTTS()
