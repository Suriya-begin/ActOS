# ActOS — AI Voice Operating System

A multilingual AI-native voice operating system that understands Tamil, Tanglish, English,
Hindi, Telugu, Malayalam and controls apps, browsers, and devices through natural speech.

## Project Structure

```
actos/
├── frontend/          # Next.js 14 + TypeScript + TailwindCSS + ShadCN + Framer Motion
├── backend/           # Python FastAPI + LangChain + LangGraph + CrewAI
├── mobile/            # Kotlin Android Accessibility Service
├── infra/             # Docker + Kubernetes + Terraform + Kafka
└── README.md
```

## Tech Stack (Strictly from Blueprint)

### Frontend
- Next.js 14 (App Router)
- TypeScript
- TailwindCSS
- ShadCN UI
- Framer Motion

### AI Brain
- Python 3.11
- FastAPI
- LangChain
- LangGraph
- CrewAI
- OpenAI APIs
- HuggingFace Transformers
- PyTorch

### Voice AI
- Whisper Large V3
- Deepgram
- ElevenLabs
- WebRTC
- Web Audio API

### Automation
- Playwright
- Puppeteer
- PyAutoGUI
- RobotJS

### Mobile
- Kotlin
- Android Accessibility APIs
- ADB

### Systems
- Rust (security-critical modules)

### Distributed
- Apache Kafka
- NATS
- gRPC
- WebSockets

### Database
- PostgreSQL (primary)
- Redis (cache)
- Pinecone (vector)
- Weaviate (vector backup)

### Cloud
- AWS EC2, S3, RDS, CloudFront, Lambda
- Docker
- Kubernetes
- Terraform

### Security
- Auth.js
- Clerk
- JWT
- Voice Biometrics

## Quick Start

### 1. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```

### 3. Infrastructure
```bash
cd infra/docker
docker-compose up -d
```

## Phases
- Phase 1 — MVP Foundation (Voice + STT + Playwright + Auth)
- Phase 2 — Intelligent Assistant (Memory + Agents + Conversations)
- Phase 3 — Universal Automation (Desktop + Android + ADB)
- Phase 4 — AI Operating System (Vision + Autonomous Planning)
- Phase 5 — Cloud Ecosystem (Kafka + K8s + Terraform + AWS)
