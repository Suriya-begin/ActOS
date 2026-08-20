from loguru import logger
from app.core.intent_extractor import ExtractedIntent

class ReminderAgent:
    def __init__(self):
        logger.info("Reminder Agent stub initialized")

    async def execute(self, intent: ExtractedIntent, memory_context: dict, user_id: str) -> dict:
        logger.info(f"Reminder Agent executing: {intent.action}")
        return {
            "success": True,
            "message": f"Reminder task '{intent.action}' executed successfully (Stub)."
        }
