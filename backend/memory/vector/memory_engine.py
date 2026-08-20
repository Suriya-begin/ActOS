# ============================================================
# ActOS — Vector Memory Engine
# Tech Stack: Pinecone + sentence-transformers + PostgreSQL
# Stores: contacts, preferences, routines, conversation history
# ============================================================

from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from langchain_openai import OpenAIEmbeddings
import json
import uuid
from datetime import datetime
from loguru import logger
from typing import Any

from app.core.config import settings


class MemoryEngine:
    """
    Pinecone Vector Memory Engine
    
    What it stores:
    - Contacts: "Amma" → {phone, platform, language_pref}
    - Preferences: "preferred music" → "AR Rahman, Lofi"
    - Routines: "morning_routine" → {steps, time}
    - Conversation history → vector embeddings for retrieval
    - Past commands → for pattern learning
    
    How it works:
    1. Every memory item = text → embedding vector → stored in Pinecone
    2. On recall: query text → embedding → similarity search in Pinecone
    3. Top-k results returned as context to agents
    """

    MEMORY_TYPES = ["contact", "preference", "routine", "habit", "task", "conversation"]

    def __init__(self):
        # Pinecone client
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX
        self._init_index()

        # Local sentence transformer for fast embeddings
        try:
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Local SentenceTransformer initialized successfully.")
        except Exception as e:
            self.embedder = None
            logger.warning(f"⚠️ Failed to load local SentenceTransformer: {e}. Using OpenAI/Zero fallback.")

        # OpenAI embeddings (higher quality, slower)
        try:
            self.openai_embedder = OpenAIEmbeddings(
                api_key=settings.OPENAI_API_KEY,
                model="text-embedding-3-small",
            )
        except Exception as e:
            self.openai_embedder = None
            logger.warning(f"⚠️ OpenAI embeddings not available: {e}")

        logger.info("✅ Memory Engine initialized (Pinecone)")

    def _init_index(self):
        """Create Pinecone index if it doesn't exist"""
        try:
            existing = [i.name for i in self.pc.list_indexes()]
            if self.index_name not in existing:
                self.pc.create_index(
                    name=self.index_name,
                    dimension=1536,         # OpenAI embedding dimension
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )
                logger.info(f"✅ Pinecone index '{self.index_name}' created")
            self.index = self.pc.Index(self.index_name)
        except Exception as e:
            logger.error(f"❌ Pinecone index initialization failed: {e}")
            self.index = None

    async def embed(self, text: str) -> list[float]:
        """Convert text to embedding vector with safe fallbacks"""
        if self.embedder:
            try:
                vector = self.embedder.encode(text).tolist()
                if len(vector) < 1536:
                    vector = vector + [0.0] * (1536 - len(vector))
                return vector[:1536]
            except Exception as e:
                logger.error(f"Local embedder failed: {e}")

        if self.openai_embedder and settings.OPENAI_API_KEY != "mock-key":
            try:
                return await self.openai_embedder.aembed_query(text)
            except Exception as e:
                logger.error(f"OpenAI embedder failed: {e}")

        # Safe fallback: return a vector with a tiny non-zero value to prevent Pinecone only-zeros error
        return [1e-9] + [0.0] * 1535

    async def store(
        self,
        user_id: str,
        key: str,
        value: Any,
        memory_type: str = "preference",
    ):
        """
        Store a memory item in Pinecone
        """
        if not self.index:
            logger.warning("⚠️ Pinecone index not initialized. Memory store skipped.")
            return

        try:
            vector_id = f"{user_id}_{memory_type}_{key}_{uuid.uuid4().hex[:8]}"
            text_to_embed = f"{memory_type}: {key} = {json.dumps(value)}"
            vector = await self.embed(text_to_embed)

            self.index.upsert(vectors=[{
                "id": vector_id,
                "values": vector,
                "metadata": {
                    "user_id": user_id,
                    "memory_type": memory_type,
                    "key": key,
                    "value": json.dumps(value),
                    "created_at": datetime.utcnow().isoformat(),
                }
            }])
            logger.info(f"💾 Memory stored: [{memory_type}] {key} for user {user_id}")
        except Exception as e:
            logger.error(f"❌ Failed to store memory in Pinecone: {e}")

    async def recall(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        memory_type: str = None,
    ) -> dict:
        """
        Recall relevant memories for a query
        """
        memories = {}
        if not self.index:
            logger.warning("⚠️ Pinecone index not initialized. Memory recall skipped.")
            # Still recall contacts if possible
            memories["contacts"] = {}
            return memories

        try:
            vector = await self.embed(query)

            filter_dict = {"user_id": {"$eq": user_id}}
            if memory_type:
                filter_dict["memory_type"] = {"$eq": memory_type}

            results = self.index.query(
                vector=vector,
                top_k=limit,
                include_metadata=True,
                filter=filter_dict,
            )

            for match in results.matches:
                if match.score > 0.6:  # Only high-confidence matches
                    meta = match.metadata
                    key = meta.get("key", "")
                    try:
                        value = json.loads(meta.get("value", "{}"))
                    except Exception:
                        value = meta.get("value", "")

                    memories[key] = {
                        "value": value,
                        "type": meta.get("memory_type"),
                        "score": match.score,
                    }
        except Exception as e:
            logger.error(f"❌ Failed to query Pinecone: {e}")

        # Always include contacts in recall
        contacts = await self._recall_contacts(user_id)
        memories["contacts"] = contacts

        logger.info(f"💾 Memory recalled: {len(memories)} items for query '{query[:40]}'")
        return memories

    async def _recall_contacts(self, user_id: str) -> dict:
        """Specifically recall all stored contacts for a user"""
        contacts = {}
        if not self.index:
            return contacts

        try:
            vector = await self.embed("contact phone whatsapp call message")
            results = self.index.query(
                vector=vector,
                top_k=20,
                include_metadata=True,
                filter={
                    "user_id": {"$eq": user_id},
                    "memory_type": {"$eq": "contact"},
                },
            )
            for match in results.matches:
                meta = match.metadata
                try:
                    value = json.loads(meta.get("value", "{}"))
                except Exception:
                    value = {}
                contacts[meta.get("key", "").lower()] = value
        except Exception as e:
            logger.error(f"❌ Failed to recall contacts from Pinecone: {e}")
        return contacts

    async def remember_contact(
        self,
        user_id: str,
        name: str,
        phone: str = None,
        platform: str = "whatsapp",
        language_pref: str = "tamil",
        extra: dict = None,
    ):
        """
        Store a contact in memory
        """
        value = {
            "phone": phone,
            "platform": platform,
            "language_pref": language_pref,
            **(extra or {}),
        }
        await self.store(user_id, name, value, memory_type="contact")
        logger.info(f"👤 Contact stored: {name} for user {user_id}")

    async def remember_preference(
        self,
        user_id: str,
        preference_key: str,
        preference_value: Any,
    ):
        """
        Store user preference
        """
        await self.store(user_id, preference_key, preference_value, memory_type="preference")

    async def delete_memory(self, user_id: str, key: str):
        """Delete a specific memory item"""
        if not self.index:
            return

        try:
            vector = await self.embed(key)
            results = self.index.query(
                vector=vector,
                top_k=5,
                include_metadata=True,
                filter={"user_id": {"$eq": user_id}, "key": {"$eq": key}},
            )
            ids = [m.id for m in results.matches]
            if ids:
                self.index.delete(ids=ids)
                logger.info(f"🗑️ Memory deleted: {key} for user {user_id}")
        except Exception as e:
            logger.error(f"❌ Failed to delete memory from Pinecone: {e}")


# ── Singleton ──
memory_engine = MemoryEngine()
