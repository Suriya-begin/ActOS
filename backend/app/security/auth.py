"""
ActOS — Security & Authentication
Blueprint: Auth.js + Clerk + JWT + Voice Biometrics + Zero-Trust Execution
"""
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.core.config import settings
from loguru import logger

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── JWT TOKEN MANAGEMENT ──────────────────────────────────────────────────────

def create_access_token(user_id: str, email: str) -> str:
    """Create JWT token for authenticated user."""
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": user_id, "email": email, "exp": expire, "iat": datetime.utcnow()}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """FastAPI dependency — extract current user from JWT."""
    return verify_token(credentials.credentials)


# ── ZERO-TRUST ACTION GATE ────────────────────────────────────────────────────

SENSITIVE_ACTIONS = {
    "send_message", "make_call", "make_payment",
    "book_service", "share_data", "delete_content",
    "send_email", "transfer_money",
}

def requires_auth(intent: dict) -> bool:
    """
    Blueprint: Zero-trust — check if action needs user confirmation.
    Sensitive actions ALWAYS require explicit user confirmation.
    """
    action = intent.get("intent", "").lower()
    app    = intent.get("app", "").lower()

    if action in SENSITIVE_ACTIONS:
        return True
    if intent.get("requires_auth", False):
        return True
    # Payments always blocked for auto-execution
    if app in {"paytm", "gpay", "phonepe", "bank"}:
        return True
    return False


# ── VOICE BIOMETRIC VERIFICATION ─────────────────────────────────────────────

class VoiceBiometrics:
    """
    Blueprint: Speaker Recognition for voice authentication.
    Uses HuggingFace speaker verification model.
    Phase 2+ feature — verifies user identity before sensitive actions.
    """

    async def enroll(self, user_id: str, audio_bytes: bytes) -> str:
        """Enroll user voice profile."""
        # TODO Phase 2: Use pyannote/speaker-diarization or resemblyzer
        # from resemblyzer import VoiceEncoder
        # encoder = VoiceEncoder()
        # voice_embedding = encoder.embed_utterance(wav)
        logger.info(f"Voice enrollment queued for user {user_id}")
        return f"voice_profile_{user_id}"

    async def verify(self, user_id: str, audio_bytes: bytes, voice_profile_id: str) -> bool:
        """
        Verify speaker identity.
        Blueprint: voice biometrics before sensitive actions.
        Returns True if voice matches enrolled profile.
        """
        # TODO Phase 2: Compare embeddings using cosine similarity
        # For Phase 1: returns True (stub) — implement in Phase 2
        logger.warning("Voice biometric verification: STUB — implement in Phase 2")
        return True

    async def request_confirmation(self, action_description: str) -> dict:
        """
        Blueprint: Confirmation-based actions — ask user before executing.
        Returns confirmation request to send to frontend via WebSocket.
        """
        return {
            "type":        "auth_required",
            "message":     f"Confirm: {action_description}?",
            "action":      action_description,
            "options":     ["confirm", "cancel"],
            "timeout_sec": 30,
        }


voice_biometrics = VoiceBiometrics()
