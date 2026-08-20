============================================================
  ActOS — AI Voice Operating System
  Complete Project Structure
============================================================

TECH STACK (as defined in blueprint):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Frontend Layer:
  ✅ Next.js 14 (App Router)
  ✅ TypeScript
  ✅ TailwindCSS
  ✅ ShadCN UI (Radix UI primitives)
  ✅ Framer Motion

AI Brain Layer:
  ✅ Python 3.11
  ✅ FastAPI
  ✅ LangChain
  ✅ LangGraph (state machine orchestrator)
  ✅ CrewAI (multi-agent system)
  ✅ OpenAI APIs (GPT-4o + Whisper)
  ✅ HuggingFace Transformers (sentence-transformers)
  ✅ PyTorch

Voice AI Layer:
  ✅ Whisper Large V3 (STT)
  ✅ Deepgram (streaming STT)
  ✅ ElevenLabs (TTS)
  ✅ WebRTC (browser mic capture)
  ✅ Web Audio APIs (waveform)

Automation Layer:
  ✅ Playwright (browser automation)
  ⬜ Puppeteer (Phase 3)
  ✅ PyAutoGUI (desktop automation - Phase 3)
  ⬜ RobotJS (Phase 3)

Native Mobile Layer:
  ⬜ Kotlin (Phase 3)
  ⬜ Android Accessibility APIs (Phase 3)
  ⬜ ADB (Phase 3)

Systems Programming:
  ⬜ Rust (Phase 4)

Distributed Systems:
  ⬜ Kafka (Phase 5)
  ⬜ NATS (Phase 5)
  ⬜ gRPC (Phase 5)
  ✅ WebSockets

Database Layer:
  ✅ PostgreSQL (primary)
  ✅ Redis (caching)
  ✅ Pinecone (vector DB)
  ✅ Qdrant (vector DB alternative)

Cloud & Infrastructure:
  ⬜ AWS EC2/S3/RDS (Phase 5)
  ✅ Docker
  ⬜ Kubernetes (Phase 5)
  ⬜ Terraform (Phase 5)

Security:
  ✅ JWT (python-jose)
  ✅ Clerk (frontend auth)
  ✅ passlib/bcrypt
  ⬜ Voice Biometrics (Phase 2 extension)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROJECT STRUCTURE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

actos/
├── backend/
│   ├── main.py                          ✅ FastAPI entry point
│   ├── requirements.txt                 ✅ All Python dependencies
│   ├── Dockerfile                       ✅ Backend container
│   ├── .env.example                     ✅ Environment template
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py                ✅ Pydantic Settings
│   │   │   ├── database.py              ✅ PostgreSQL + SQLAlchemy
│   │   │   ├── redis_client.py          ✅ Redis cache
│   │   │   ├── intent_extractor.py      ✅ LangChain + GPT-4o NLU
│   │   │   └── orchestrator.py          ✅ LangGraph state machine
│   │   └── api/routes/
│   │       ├── voice.py                 ✅ REST voice endpoints
│   │       └── websocket.py             ✅ WS real-time pipeline
│   ├── voice/
│   │   ├── stt/whisper_engine.py        ✅ Whisper + Deepgram STT
│   │   └── tts/elevenlabs_engine.py     ✅ ElevenLabs TTS
│   ├── agents/
│   │   ├── messaging/whatsapp_agent.py  ✅ Playwright WhatsApp
│   │   ├── browser/browser_agent.py     ✅ Playwright browser
│   │   ├── calendar/                    ⬜ (scaffold below)
│   │   ├── email/                       ⬜ (scaffold below)
│   │   ├── reminder/                    ⬜ (scaffold below)
│   │   └── research/                    ⬜ (scaffold below)
│   ├── memory/
│   │   └── vector/memory_engine.py      ✅ Pinecone + embeddings
│   └── security/
│       └── auth/security_gate.py        ✅ JWT + Zero Trust
├── frontend/
│   ├── package.json                     ✅ Next.js + all deps
│   └── src/
│       └── hooks/useVoice.ts            ✅ WebRTC + WebSocket hook
└── infra/
    └── docker/docker-compose.yml        ✅ Full stack compose

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUICK START:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Clone and setup:
   cd actos/backend
   cp .env.example .env
   # Fill in: OPENAI_API_KEY, ELEVENLABS_API_KEY, DEEPGRAM_API_KEY

2. Start infrastructure:
   cd infra/docker
   docker compose up -d postgres redis

3. Start backend:
   cd backend
   pip install -r requirements.txt
   playwright install chromium
   uvicorn main:app --reload

4. Start frontend:
   cd frontend
   npm install
   npm run dev

5. Open browser:
   Frontend:  http://localhost:3000
   API Docs:  http://localhost:8000/docs
   Health:    http://localhost:8000/health

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API KEYS NEEDED:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  OPENAI_API_KEY    → platform.openai.com
  ELEVENLABS_API_KEY → elevenlabs.io
  DEEPGRAM_API_KEY  → deepgram.com
  PINECONE_API_KEY  → app.pinecone.io (free tier available)
  CLERK keys        → clerk.com (free tier available)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
