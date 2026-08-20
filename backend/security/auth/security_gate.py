# ============================================================
# ActOS — Security Gate (Zero Trust Execution)
# Tech Stack: JWT + voice biometrics + passlib
# Principle: NEVER auto-execute sensitive actions without confirmation
# ============================================================

from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from loguru import logger
import hashlib

from app.core.config import settings


# ── SENSITIVE ACTIONS — always require confirmation ──
SENSITIVE_ACTIONS = {
    "send_message",
    "make_call",
    "send_email",
    "book_cab",
    "order_food",
    "make_payment",
    "book_ticket",
    "delete_file",
    "share_data",
    "post_social",
}

# ── CRITICAL ACTIONS — require extra voice verification ──
CRITICAL_ACTIONS = {
    "make_payment",
    "bank_transfer",
    "delete_account",
    "share_location",
}


class SecurityGate:
    """
    Zero Trust Security Gate
    
    Principles:
    1. All sensitive actions need user confirmation
    2. Voice biometrics verify identity
    3. OTPs/PINs are NEVER handled by ActOS — user enters manually
    4. Every auth event is logged
    5. 3 failed attempts = lockout
    """

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        logger.info("✅ Security Gate initialized (Zero Trust)")

    # ── JWT TOKEN MANAGEMENT ──

    def create_access_token(self, user_id: str, extra: dict = None) -> str:
        """Create JWT access token"""
        payload = {
            "sub": user_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            ),
            **(extra or {}),
        }
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {e}",
            )

    # ── ACTION SECURITY CHECKS ──

    def is_sensitive(self, action: str) -> bool:
        """Check if action requires confirmation"""
        return action in SENSITIVE_ACTIONS

    def is_critical(self, action: str) -> bool:
        """Check if action requires extra voice verification"""
        return action in CRITICAL_ACTIONS

    async def check_voice_auth(self, user_id: str, action: str) -> bool:
        """
        Check if user has voice auth for this session
        For now returns False → triggers confirmation request
        In production: compares voice print against stored model
        """
        # For MVP: require explicit confirmation for everything for step-by-step guidance
        logger.info(f"🔐 Voice auth check for action: {action} by user: {user_id}")
        return False  # Always require confirmation in MVP

    def build_confirmation_message(self, intent) -> str:
        """
        Build a natural confirmation prompt
        e.g. "I'm about to send 'hi' to Ravi on WhatsApp. Confirm?"
        """
        action_map = {
            "send_message": f"send '{intent.content}' to {intent.target} on {intent.app}",
            "make_call":    f"call {intent.target} on {intent.app}",
            "send_email":   f"send an email to {intent.target}",
            "book_cab":     f"book a cab to {intent.target}",
            "order_food":   f"order food from {intent.target}",
            "play_music":   f"play '{intent.target}' on {intent.app}",
        }
        action_text = action_map.get(
            intent.action,
            f"perform '{intent.action}' on {intent.app}"
        )
        return f"I'm about to {action_text}. Should I proceed? Say yes to confirm."

    # ── PASSWORD HASHING ──

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return self.pwd_context.verify(plain, hashed)

    # ── AUDIT LOG ──

    async def log_security_event(
        self,
        user_id: str,
        event_type: str,
        action: str,
        verified: bool,
        db=None,
    ):
        """Log every security event to PostgreSQL"""
        from app.core.database import SecurityEvent
        if db:
            event = SecurityEvent(
                user_id=user_id,
                event_type=event_type,
                action_requested=action,
                verified=verified,
            )
            db.add(event)
            await db.commit()
        logger.info(
            f"🔐 Security event: [{event_type}] action={action} "
            f"user={user_id} verified={verified}"
        )


# ── JWT FastAPI Dependency ──
async def get_current_user(token: str) -> dict:
    gate = SecurityGate()
    return gate.verify_token(token)


# ── Singleton ──
security_gate = SecurityGate()
