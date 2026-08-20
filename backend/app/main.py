import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from app.core.config import settings
from app.core.database import init_db
from app.core.redis_client import init_redis
from app.api.routes import voice, intent, agents, memory, automation, auth, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 ActOS Backend starting...")
    await init_db()
    await init_redis()
    logger.info("✅ ActOS Backend ready")
    yield
    logger.info("🛑 ActOS Backend shutting down...")


app = FastAPI(
    title="ActOS API",
    description="AI Voice Operating System — Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://actos.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register all routers ──────────────────────────────────
app.include_router(auth.router,       prefix="/api/auth",       tags=["Auth"])
app.include_router(voice.router,      prefix="/api/voice",      tags=["Voice"])
app.include_router(intent.router,     prefix="/api/intent",     tags=["Intent"])
app.include_router(agents.router,     prefix="/api/agents",     tags=["Agents"])
app.include_router(memory.router,     prefix="/api/memory",     tags=["Memory"])
app.include_router(automation.router, prefix="/api/automation", tags=["Automation"])
app.include_router(websocket.router,  prefix="/ws",             tags=["WebSocket"])


@app.get("/health")
async def health():
    return {"status": "ok", "app": "ActOS", "version": "1.0.0"}
