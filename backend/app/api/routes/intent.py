"""
ActOS — Intent API Routes
POST /api/intent/extract  → Extract intent from transcript
POST /api/intent/execute  → Execute extracted intent
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.intent_extractor import intent_extractor
from app.core.orchestrator import orchestrator
from app.security.auth import get_current_user
from app.core.database import get_db
from app.db.models.command import Command
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class CommandRequest(BaseModel):
    transcript: str
    language: str = None


@router.post("/extract")
async def extract_intent(
    body: CommandRequest,
    user: dict = Depends(get_current_user),
):
    """Extract structured intent from voice transcript."""
    intent = await intent_extractor.extract(body.transcript)
    return {"intent": intent.dict(), "requires_auth": intent.needs_auth}


@router.post("/execute")
async def execute_command(
    body: CommandRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Full pipeline: transcript → intent → orchestrator execution.
    Returns result.
    """
    user_id = user["sub"]
    session_id = f"sess_{user_id}"

    # 1. Extract intent
    intent_obj = await intent_extractor.extract(body.transcript)
    intent_dict = intent_obj.dict()

    # 2. Run orchestrator
    orchestration_result = await orchestrator.process_command(intent_obj, user_id, session_id)
    
    voice_response = orchestration_result.get("voice_response", "Done.")
    result_data = orchestration_result.get("result", {})
    auth_needed = orchestration_result.get("auth_required", False)

    # 3. Save command to DB
    cmd = Command(
        user_id=user_id, 
        raw_text=body.transcript,
        language=intent_dict.get("language"), 
        intent=intent_dict.get("action"),
        app_target=intent_dict.get("app"), 
        params=intent_dict.get("content"),
        status="done" if not auth_needed else "pending", 
        auth_required=auth_needed
    )
    db.add(cmd)
    await db.commit()

    if auth_needed:
        return {
            "command_id":   str(cmd.id),
            "status":       "awaiting_confirmation",
            "intent":       intent_dict,
            "message":      voice_response,
        }

    return {
        "command_id": str(cmd.id), 
        "status": "done", 
        "result": voice_response, 
        "intent": intent_dict
    }
