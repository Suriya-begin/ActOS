"""
ActOS — Deepgram Realtime Streaming STT
Blueprint: Deepgram for low-latency live transcription via WebSocket
"""
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from app.core.config import settings
from loguru import logger


class DeepgramStream:
    """
    Streams mic audio → Deepgram → live transcript.
    Used for continuous listening and wake-word detection.
    """
    def __init__(self):
        self.client = DeepgramClient(settings.DEEPGRAM_API_KEY)

    async def start_stream(self, on_transcript_callback):
        connection = self.client.listen.live.v("1")

        def on_message(self_inner, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            if sentence:
                on_transcript_callback(sentence)

        connection.on(LiveTranscriptionEvents.Transcript, on_message)
        options = LiveOptions(model="nova-2", language="hi", smart_format=True, interim_results=True, endpointing=300)
        connection.start(options)
        return connection

    async def send_audio(self, connection, audio_chunk: bytes):
        connection.send(audio_chunk)


deepgram_stream = DeepgramStream()
