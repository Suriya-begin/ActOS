"""
ActOS — Memory Engine
Blueprint: Phase 2 — remembers contacts, preferences, routines, past conversations
"""
from app.memory.vector_store import vector_store
from app.core.redis_client import get_redis
from app.core.database import AsyncSessionLocal
from app.db.models.memory import Memory, Contact
from loguru import logger
import json


class MemoryEngine:
    """
    Central memory system for ActOS.
    - Short-term: Redis (current session conversation)
    - Long-term: PostgreSQL (structured data) + Pinecone (semantic search)
    """

    # ── SHORT-TERM CONVERSATION MEMORY (Redis) ────────────────────────────

    async def save_conversation_turn(self, user_id: str, role: str, text: str):
        """Save a conversation turn to Redis for context window."""
        redis = get_redis()
        key = f"conversation:{user_id}"
        history = await self.get_conversation_history(user_id)
        history.append({"role": role, "text": text})
        # Keep last 20 turns only
        if len(history) > 20:
            history = history[-20:]
        await redis.setex(key, 3600, json.dumps(history))   # 1 hour TTL

    async def get_conversation_history(self, user_id: str) -> list:
        """Get recent conversation from Redis."""
        redis = get_redis()
        key = f"conversation:{user_id}"
        data = await redis.get(key)
        return json.loads(data) if data else []

    async def clear_conversation(self, user_id: str):
        redis = get_redis()
        await redis.delete(f"conversation:{user_id}")

    # ── LONG-TERM MEMORY (PostgreSQL + Pinecone) ──────────────────────────

    async def remember(self, user_id: str, category: str, key: str, value: dict):
        """
        Store a memory in both PostgreSQL and Pinecone.
        category: contact | preference | routine | habit
        """
        # Store in Pinecone for semantic search
        vector_id = await vector_store.store_memory(user_id, category, key, value)

        # Store structured data in PostgreSQL
        async with AsyncSessionLocal() as db:
            memory = Memory(user_id=user_id, category=category, key=key, value=value, embedding_id=vector_id)
            db.add(memory)
            await db.commit()
        logger.info(f"Remembered [{category}] {key} for user {user_id}")

    async def recall(self, user_id: str, query: str) -> list:
        """Semantic recall — find relevant memories for a query."""
        return await vector_store.search_memory(user_id, query)

    async def save_contact(self, user_id: str, alias: str, name: str, phone: str = None,
                           whatsapp: str = None, email: str = None, preferred_app: str = "whatsapp"):
        """Save a contact with alias like 'Amma', 'Ravi'."""
        contact_data = {"name": name, "phone": phone, "whatsapp": whatsapp,
                        "email": email, "preferred_app": preferred_app}
        await vector_store.store_contact(user_id, alias, contact_data)

        async with AsyncSessionLocal() as db:
            contact = Contact(user_id=user_id, name=name, alias=alias, phone=phone,
                              whatsapp=whatsapp, email=email, preferred_app=preferred_app)
            db.add(contact)
            await db.commit()

    async def find_contact(self, user_id: str, name_or_alias: str) -> dict | None:
        """Find contact by name or alias — 'Amma ku message podu' → finds Amma."""
        return await vector_store.find_contact(user_id, name_or_alias)

    async def get_context_for_command(self, user_id: str, command: str) -> str:
        """
        Build full context string for LLM — conversation history + relevant memories.
        This is injected into every agent call.
        """
        history = await self.get_conversation_history(user_id)
        memories = await self.recall(user_id, command)

        context_parts = []
        if history:
            recent = history[-6:]   # last 3 turns
            context_parts.append("Recent conversation:\n" + "\n".join([f"{t['role']}: {t['text']}" for t in recent]))
        if memories:
            context_parts.append("Relevant memories:\n" + "\n".join([f"- [{m['category']}] {m['key']}: {m['value']}" for m in memories[:3]]))

        return "\n\n".join(context_parts)


memory_engine = MemoryEngine()
