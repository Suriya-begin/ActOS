from loguru import logger
from app.core.intent_extractor import ExtractedIntent

class EmailAgent:
    def __init__(self):
        logger.info("Email Agent stub initialized")

    async def execute(self, intent: ExtractedIntent, memory_context: dict, user_id: str) -> dict:
        logger.info(f"Email Agent executing: {intent.action}")
        return {
            "success": True,
            "message": f"Email task '{intent.action}' executed successfully (Stub)."
        }
