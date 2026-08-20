"""ActOS — Automation Routes"""
from fastapi import APIRouter, Depends
from app.automation.browser.playwright_engine import playwright_engine
from app.security.auth import get_current_user

router = APIRouter()

@router.post("/browser/open")
async def open_url(body: dict, user: dict = Depends(get_current_user)):
    return await playwright_engine.open_url(body["url"])

@router.post("/browser/search/amazon")
async def search_amazon(body: dict, user: dict = Depends(get_current_user)):
    return await playwright_engine.search_amazon(body["query"])

@router.post("/browser/youtube/play")
async def youtube_play(body: dict, user: dict = Depends(get_current_user)):
    return await playwright_engine.youtube_play(body["query"])
