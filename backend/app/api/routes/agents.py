"""ActOS — Agents Status Routes"""
from fastapi import APIRouter, Depends
from app.security.auth import get_current_user

router = APIRouter()

AGENT_STATUS = {
    "messaging": "online", "browser": "busy",
    "calendar": "online", "research": "offline",
    "email": "online", "reminder": "online",
}

@router.get("/status")
async def agents_status(user: dict = Depends(get_current_user)):
    return {"agents": AGENT_STATUS}
