"""
ActOS — Whisper Large V3 Speech-to-Text
Blueprint: Whisper Large V3 for Tamil/Tanglish/English/Hindi transcription
"""
import whisper
import tempfile, os
from loguru import logger
from app.core.config import settings


class WhisperEngine:
    """
    OpenAI Whisper Large V3.
    Auto-detects Tamil, Tanglish, English, Hindi, Telugu, Malayalam.
    """
    def __init__(self):
        self.model = None

    def load(self):
        logger.info(f"Loading Whisper {settings.WHISPER_MODEL} on {settings.WHISPER_DEVICE}...")
        self.model = whisper.load_model(settings.WHISPER_MODEL, device=settings.WHISPER_DEVICE, in_memory=False)
        logger.info("✅ Whisper loaded")

    def _ensure_loaded(self):
        if self.model is None:
            self.load()

    # Gemini phrases that indicate silence or noise (hallucination filter)
    _SILENCE_PHRASES = [
        "", "[silence]", "[noise]", "[background noise]", "[music]",
        "[inaudible]", "(silence)", "(noise)", "[no speech]", "no speech detected",
        "the audio", "audio file", "i cannot", "i'm unable", "unable to transcribe",
        "there is no", "there's no", "no audio", "audio contains", "the recording",
        "i don't hear", "i do not hear", "[blank", "blank audio",
    ]

    async def transcribe_bytes(self, audio_bytes: bytes, language: str = None, format: str = "webm") -> dict:
        """Transcribe raw audio bytes — returns {text, language, segments}"""
        # ── Guard: skip tiny/silent buffers ──
        # Anything under ~3KB is almost certainly silence or a mic click with no speech
        MIN_AUDIO_BYTES = 3000
        if len(audio_bytes) < MIN_AUDIO_BYTES:
            logger.info(f"Audio too short ({len(audio_bytes)} bytes) — skipping transcription")
            return {"text": "", "language": "en", "segments": []}

        mime_map = {
            "webm": "audio/webm",
            "mp4": "audio/mp4",
            "m4a": "audio/mp4",
            "wav": "audio/wav",
            "ogg": "audio/ogg",
            "mp3": "audio/mp3",
            "mpeg": "audio/mpeg"
        }
        mime_type = mime_map.get(format.lower(), "audio/webm")

        gemini_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            import httpx
            import base64
            logger.info(f"Transcribing {len(audio_bytes)} bytes using Gemini Multimodal API ({mime_type})...")
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                headers = {"Content-Type": "application/json"}
                
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                
                payload = {
                    "contents": [{
                        "parts": [
                            {
                                "inlineData": {
                                    "mimeType": mime_type,
                                    "data": audio_b64
                                }
                            },
                            {
                                "text": (
                                    "You are a speech-to-text engine. Transcribe the human speech in this audio EXACTLY as spoken.\n"
                                    "Rules:\n"
                                    "1. If the audio contains Tamil or a mix of Tamil and English (Tanglish), transcribe it using ROMANIZED English letters. "
                                    "   Examples: 'WhatsApp la message podu', 'YouTube poi AR Rahman songs play pannu', 'pause pannu', 'Google la weather search pannu'\n"
                                    "2. If the audio contains only English, transcribe it in English.\n"
                                    "3. If the audio contains Hindi, transcribe it in romanized Hindi (e.g., 'gaana play karo').\n"
                                    "4. CRITICAL: If there is NO clear human speech (only silence, background noise, music, breathing, or inaudible sounds), "
                                    "   respond with ONLY the word: SILENCE\n"
                                    "5. Do NOT add any explanation, punctuation beyond natural sentence ends, or extra words — output ONLY the transcribed speech or SILENCE."
                                )
                            }
                        ]
                    }]
                }
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, json=payload, timeout=25)
                    response.raise_for_status()
                    res_data = response.json()
                    
                    raw_transcript = ""
                    if "candidates" in res_data and res_data["candidates"]:
                        candidate = res_data["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            raw_transcript = "".join([part.get("text", "") for part in parts]).strip()
                    
                    # Strip quotes/formatting
                    transcript = raw_transcript.strip('"`\' \n')

                    # ── Hallucination / silence filter ──
                    t_lower = transcript.lower()
                    is_silence = (
                        not transcript
                        or t_lower == "silence"
                        or any(t_lower.startswith(p) or t_lower == p for p in self._SILENCE_PHRASES)
                        or len(transcript.split()) < 1  # literally empty after strip
                    )

                    if is_silence:
                        logger.info(f"Gemini returned silence/noise indicator: '{raw_transcript}' — treating as empty")
                        return {"text": "", "language": "en", "segments": []}

                    logger.info(f"Gemini transcription success: '{transcript}'")
                    # Detect language from script (Tamil unicode block) vs romanized
                    has_tamil_script = any(0x0B80 <= ord(c) <= 0x0BFF for c in transcript)
                    detected_language = "ta" if has_tamil_script else "en"
                    return {
                        "text": transcript,
                        "language": detected_language,
                        "segments": []
                    }
            except Exception as e:
                logger.error(f"Gemini transcription failed: {e}. Falling back to Deepgram...")

        if settings.DEEPGRAM_API_KEY:
            import httpx
            logger.info(f"Transcribing audio using Deepgram HTTP API ({mime_type})...")
            try:
                url = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true"
                if language:
                    url += f"&language={language}"
                else:
                    url += "&detect_language=true"
                
                headers = {
                    "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
                    "Content-Type": mime_type
                }
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, content=audio_bytes, timeout=15)
                    response.raise_for_status()
                    data = response.json()
                    transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
                    
                    detected_language = "en"
                    if "languages" in data["results"] and data["results"]["languages"]:
                        detected_language = data["results"]["languages"][0]
                    elif "channels" in data["results"] and data["results"]["channels"]:
                        detected_language = data["results"]["channels"][0].get("detected_language", "en")
                    
                    logger.info(f"Deepgram transcription success: '{transcript}' (lang: {detected_language})")
                    return {
                        "text": transcript.strip(),
                        "language": detected_language,
                        "segments": []
                    }
            except Exception as e:
                logger.error(f"Deepgram transcription failed: {e}. Falling back to local Whisper.")

        # Local Whisper fallback
        self._ensure_loaded()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        try:
            result = self.model.transcribe(tmp_path, language=language, task="transcribe", fp16=False)
            return {"text": result["text"].strip(), "language": result.get("language", "unknown"), "segments": result.get("segments", [])}
        finally:
            os.unlink(tmp_path)

    async def transcribe_file(self, file_path: str) -> dict:
        self._ensure_loaded()
        result = self.model.transcribe(file_path, fp16=False)
        return {"text": result["text"].strip(), "language": result.get("language", "unknown")}


whisper_engine = WhisperEngine()
