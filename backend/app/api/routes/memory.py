"""ActOS — Memory API Routes"""
from fastapi import APIRouter, Depends
from app.memory.memory_engine import memory_engine
from app.security.auth import get_current_user

router = APIRouter()

@router.get("/recall")
async def recall(query: str, user: dict = Depends(get_current_user)):
    results = await memory_engine.recall(user["sub"], query)
    return {"results": results}

@router.post("/contact")
async def save_contact(body: dict, user: dict = Depends(get_current_user)):
    await memory_engine.save_contact(user["sub"], body["alias"], body["name"],
                                     body.get("phone"), body.get("whatsapp"), body.get("email"))
    return {"status": "saved"}

@router.get("/history")
async def conversation_history(user: dict = Depends(get_current_user)):
    history = await memory_engine.get_conversation_history(user["sub"])
    return {"history": history}
