"""
ActOS — ElevenLabs TTS Engine
Blueprint: ElevenLabs for natural multilingual voice replies
Fallback: gTTS with automatic language detection
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from app.core.config import settings
from loguru import logger

_executor = ThreadPoolExecutor(max_workers=2)


def _detect_language_from_text(text: str, hint_language: str = None) -> str:
    """
    Detect language for gTTS from text content and optional hint.
    Returns gTTS language code.
    """
    # Use hint if provided
    if hint_language:
        lang_map = {
            "tamil": "ta",
            # Tanglish is romanized Tamil+English — 'en' TTS reads it correctly
            "tanglish": "en",
            "hindi": "hi",
            "telugu": "te",
            "malayalam": "ml",
            "english": "en",
            "kannada": "kn",
        }
        code = lang_map.get(hint_language.lower())
        if code:
            return code

    text_lower = text.lower()

    # Check for Tamil Unicode script characters
    if any(0x0B80 <= ord(c) <= 0x0BFF for c in text):
        return "ta"

    # Check for Hindi/Devanagari Unicode
    if any(0x0900 <= ord(c) <= 0x097F for c in text):
        return "hi"

    # Check for Telugu Unicode
    if any(0x0C00 <= ord(c) <= 0x0C7F for c in text):
        return "te"

    # Tamil/Tanglish keywords (romanized)
    tamil_keywords = [
        "pannu", "podu", "panni", "sollu", "irukku", "vaanga", "nandri",
        "sari", "illai", "vena", "paaru", "vandhu", "poi", "vandhom",
        "therikuthu", "aagurom", "pannurom", "paatom", "thodangu",
        "niruthu", "off pannu", "on pannu", "paattu", "koodava"
    ]
    if any(kw in text_lower for kw in tamil_keywords):
        return "ta"

    # Hindi keywords
    hindi_keywords = [
        "karo", "karein", "hai", "hoon", "theek", "nahi", "haan",
        "chalao", "band", "chalu", "bolo", "sun", "dekh", "jao"
    ]
    if any(kw in text_lower for kw in hindi_keywords):
        return "hi"

    return "en"


class ElevenLabsEngine:
    def __init__(self):
        self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        self.voice_id = settings.ELEVENLABS_VOICE_ID

    async def speak(self, text: str, language: str = None) -> bytes:
        """Convert text → MP3 audio bytes to stream to browser."""
        logger.info(f"TTS generating: '{text[:60]}' (lang={language})")

        # Try ElevenLabs only if API key is set and not obviously a free/invalid key
        if settings.ELEVENLABS_API_KEY and settings.ELEVENLABS_API_KEY not in ("", "your_key_here", "None", "none"):
            try:
                loop = asyncio.get_event_loop()
                audio_bytes = await loop.run_in_executor(
                    _executor,
                    self._elevenlabs_sync,
                    text
                )
                return audio_bytes
            except Exception as e:
                err_str = str(e)
                if "402" in err_str or "payment_required" in err_str or "paid_plan" in err_str:
                    logger.warning("⚠️ ElevenLabs requires paid plan — switching permanently to gTTS.")
                    # Disable further ElevenLabs attempts this session
                    settings.ELEVENLABS_API_KEY = ""
                else:
                    logger.warning(f"⚠️ ElevenLabs failed: {e}. Falling back to gTTS...")

        # gTTS fallback (always available, no API key needed)
        try:
            from gtts import gTTS
            import io

            detected_lang = _detect_language_from_text(text, language)
            logger.info(f"gTTS generating speech: lang={detected_lang}")

            fp = io.BytesIO()
            tts = gTTS(text=text, lang=detected_lang, slow=False)
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except Exception as gtts_err:
            logger.error(f"❌ gTTS failed: {gtts_err}")
            raise gtts_err

    def _elevenlabs_sync(self, text: str) -> bytes:
        """Synchronous ElevenLabs call (run in executor)"""
        audio = self.client.generate(
            text=text,
            voice=self.voice_id,
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.8,
                style=0.2,
                use_speaker_boost=True
            ),
            model="eleven_multilingual_v2",  # Supports Tamil/Hindi/Telugu
        )
        return b"".join(audio)


elevenlabs_engine = ElevenLabsEngine()
