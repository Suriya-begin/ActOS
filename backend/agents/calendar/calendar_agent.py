from loguru import logger
from app.core.intent_extractor import ExtractedIntent

class CalendarAgent:
    def __init__(self):
        logger.info("Calendar Agent stub initialized")

    async def execute(self, intent: ExtractedIntent, memory_context: dict, user_id: str) -> dict:
        logger.info(f"Calendar Agent executing: {intent.action}")
        return {
            "success": True,
            "message": f"Calendar task '{intent.action}' executed successfully (Stub)."
        }
