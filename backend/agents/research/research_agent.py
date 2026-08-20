from loguru import logger
from app.core.intent_extractor import ExtractedIntent

class ResearchAgent:
    def __init__(self):
        logger.info("Research Agent stub initialized")

    async def execute(self, intent: ExtractedIntent, memory_context: dict, user_id: str) -> dict:
        logger.info(f"Research Agent executing: {intent.action}")
        return {
            "success": True,
            "message": f"Research task '{intent.action}' executed successfully (Stub)."
        }
