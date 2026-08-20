"""
ActOS — Redis Client
Blueprint: Redis for caching, session state, conversation history
"""
import redis.asyncio as aioredis
from app.core.config import settings
from loguru import logger

class MockRedis:
    """In-memory Redis fallback to prevent server crashes if local Redis is missing."""
    def __init__(self):
        self.store = {}
        logger.warning("⚠️ Using local in-memory MockRedis (short-term conversation history won't persist across restarts).")

    async def ping(self):
        return True

    async def setex(self, key: str, time: int, value: str):
        self.store[key] = value
        return True

    async def get(self, key: str) -> str:
        return self.store.get(key)

    async def delete(self, *keys: str) -> int:
        count = 0
        for key in keys:
            if key in self.store:
                del self.store[key]
                count += 1
        return count


redis_client = None


async def init_redis():
    global redis_client
    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        # Verify connection
        await redis_client.ping()
        logger.info("✅ Redis connected successfully")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        redis_client = MockRedis()


def get_redis():
    return redis_client

