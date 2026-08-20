"""
ActOS — Auth Routes (Email/Password + JWT)
Real production-grade registration and login.
No Clerk, no external OAuth — pure JWT + bcrypt.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.db.models.user import User
from app.security.auth import (
    create_access_token,
    verify_token,
    pwd_context,
)
import uuid

router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str = ""
    last_name:  str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    email: EmailStr
    first_name: str = ""
    last_name:  str = ""


class AuthResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user: dict


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/google", response_model=AuthResponse)
async def google_auth(body: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate or register a user logging in via Google OAuth."""
    email_lower = body.email.lower()
    result = await db.execute(select(User).where(User.email == email_lower))
    user: User | None = result.scalar_one_or_none()

    if not user:
        # User doesn't exist, create a new one with a random placeholder password
        # Since hashed_password is not nullable, we store a securely generated random string
        random_password = str(uuid.uuid4())
        user = User(
            id             = uuid.uuid4(),
            email          = email_lower,
            hashed_password= pwd_context.hash(random_password),
            first_name     = body.first_name.strip(),
            last_name      = body.last_name.strip(),
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Contact support."
        )

    token = create_access_token(str(user.id), user.email)
    return AuthResponse(
        access_token=token,
        user=_user_dict(user),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user with email + password."""
    # Check duplicate
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    if len(body.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters."
        )

    user = User(
        id             = uuid.uuid4(),
        email          = body.email.lower(),
        hashed_password= pwd_context.hash(body.password),
        first_name     = body.first_name.strip(),
        last_name      = body.last_name.strip(),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token = create_access_token(str(user.id), user.email)
    return AuthResponse(
        access_token=token,
        user=_user_dict(user),
    )


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with email + password, return JWT."""
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user: User | None = result.scalar_one_or_none()

    if not user or not pwd_context.verify(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Contact support."
        )

    token = create_access_token(str(user.id), user.email)
    return AuthResponse(
        access_token=token,
        user=_user_dict(user),
    )


@router.get("/me")
async def me(token: str):
    """Verify token and return current user payload."""
    payload = verify_token(token)
    return {"valid": True, "user": payload}


# ── Helpers ───────────────────────────────────────────────────

def _user_dict(user: User) -> dict:
    full = f"{user.first_name} {user.last_name}".strip() or user.email.split("@")[0]
    return {
        "id":         str(user.id),
        "email":      user.email,
        "firstName":  user.first_name or "",
        "lastName":   user.last_name or "",
        "fullName":   full,
        "avatar":     (user.first_name or user.email)[0].upper(),
        "createdAt":  str(user.created_at),
    }
