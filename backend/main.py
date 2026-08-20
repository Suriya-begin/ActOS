# ============================================================
# ActOS — FastAPI Main Application
# Tech Stack: FastAPI + WebSockets + LangGraph + CrewAI
# ============================================================

import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger

from app.core.config import settings
from app.core.database import init_db
from app.core.redis_client import init_redis
from app.api.routes import voice, agents, memory, auth, automation, websocket
from app.core.events import startup_event, shutdown_event


# ── LIFESPAN (startup + shutdown) ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    logger.info("🚀 ActOS Backend starting up...")
    await init_db()
    await init_redis()
    await startup_event()
    logger.info("✅ ActOS Backend ready — AI Voice OS is live")
    yield
    # SHUTDOWN
    logger.info("🔴 ActOS Backend shutting down...")
    await shutdown_event()


# ── FASTAPI APP ──
app = FastAPI(
    title="ActOS — AI Voice Operating System",
    description="Multilingual AI Voice OS Backend — Tamil, Tanglish, English & more",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ── CORS (Next.js frontend) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # Next.js dev (port 3000)
        "http://localhost:3001",   # Next.js dev (port 3001 fallback)
        "http://localhost:3002",   # Next.js dev (port 3002 fallback)
        "https://actos.app",       # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── ROUTES ──
app.include_router(voice.router,      prefix="/api/v1/voice",      tags=["Voice AI"])
app.include_router(agents.router,     prefix="/api/v1/agents",     tags=["AI Agents"])
app.include_router(memory.router,     prefix="/api/v1/memory",     tags=["Memory Engine"])
app.include_router(auth.router,       prefix="/api/v1/security",   tags=["Security"])
app.include_router(auth.router,       prefix="/api/auth",          tags=["Auth"])   # Frontend-compatible path
app.include_router(automation.router, prefix="/api/v1/automation", tags=["Automation"])
app.include_router(websocket.router,  prefix="/ws",                tags=["WebSocket"])


# ── HEALTH CHECK ──
@app.get("/health")
async def health():
    return {
        "status": "online",
        "service": "ActOS Backend",
        "version": "1.0.0",
        "stack": {
            "api": "FastAPI",
            "ai": "LangGraph + CrewAI + GPT-4o",
            "voice_stt": "Whisper Large V3 + Deepgram",
            "voice_tts": "ElevenLabs",
            "memory": "Pinecone + PostgreSQL",
            "cache": "Redis",
            "automation": "Playwright + PyAutoGUI",
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
