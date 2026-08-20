"""
ActOS — Central Configuration
Loads all environment variables via pydantic-settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ActOS"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me"
    APP_PORT: int = 8000
    PLAYWRIGHT_HEADLESS: bool = False
    PLAYWRIGHT_SLOWMO: int = 0

    # OpenAI
    OPENAI_API_KEY: str = "mock-key"
    OPENAI_MODEL: str = "gpt-4o"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Whisper
    WHISPER_MODEL: str = "large-v3"
    WHISPER_DEVICE: str = "cpu"

    # Deepgram
    DEEPGRAM_API_KEY: str = ""

    # ElevenLabs
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"

    # PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://actos_user:actos_password@localhost:5432/actos_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_ENV: str = "us-east-1-aws"
    PINECONE_INDEX: str = "actos-memory"

    # Weaviate
    WEAVIATE_URL: str = "http://localhost:8080"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_COMMANDS: str = "actos.commands"
    KAFKA_TOPIC_RESULTS: str = "actos.results"
    KAFKA_TOPIC_EVENTS: str = "actos.events"

    # NATS
    NATS_URL: str = "nats://localhost:4222"

    # JWT
    JWT_SECRET: str = "change-me-jwt"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # Clerk
    CLERK_SECRET_KEY: str = ""
    CLERK_PUBLISHABLE_KEY: str = ""

    # AWS
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-south-1"
    AWS_S3_BUCKET: str = "actos-assets"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

import os
if not os.environ.get("OPENAI_API_KEY") and settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY


def get_llm(temperature: float = 0):
    """
    Get configured ChatOpenAI instance.
    Uses Google's OpenAI-compatible endpoint if GEMINI_API_KEY is available.
    """
    from langchain_openai import ChatOpenAI
    gemini_key = os.environ.get("GEMINI_API_KEY") or settings.GEMINI_API_KEY
    if gemini_key:
        model = os.environ.get("GEMINI_MODEL") or settings.GEMINI_MODEL or "gemini-2.5-flash"
        if model == "gemini-1.5-flash":
            model = "gemini-2.5-flash"
        return ChatOpenAI(
            model=model,
            api_key=gemini_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            temperature=temperature
        )
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=temperature
    )

