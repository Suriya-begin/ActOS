"""
ActOS — Vector Memory Store
Blueprint: Pinecone for semantic vector search, Weaviate as backup
Used by Memory Engine to store and retrieve user preferences, contacts, routines
"""
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from app.core.config import settings
from loguru import logger
import uuid


class VectorMemoryStore:
    """
    Manages semantic memory using Pinecone.
    Every memory item is embedded and stored as a vector.
    Retrieval uses cosine similarity search.
    """

    def __init__(self):
        self.pc = None
        self.index = None
        self.embedder = None
        try:
            from langchain_openai import OpenAIEmbeddings
            self.openai_embedder = OpenAIEmbeddings(
                api_key=settings.OPENAI_API_KEY,
                model="text-embedding-3-small"
            )
        except Exception:
            self.openai_embedder = None

    def connect(self):
        """Initialize Pinecone connection and index."""
        if not settings.PINECONE_API_KEY or settings.PINECONE_API_KEY == "mock-key":
            logger.warning("PINECONE_API_KEY is mock/empty. Running without Pinecone semantic memory.")
            return
        try:
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)

            # Create index if it doesn't exist
            existing = [i.name for i in self.pc.list_indexes()]
            if settings.PINECONE_INDEX not in existing:
                self.pc.create_index(
                    name=settings.PINECONE_INDEX,
                    dimension=1536,   # text-embedding-3-small output dim
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )
                logger.info(f"Created Pinecone index: {settings.PINECONE_INDEX}")

            self.index = self.pc.Index(settings.PINECONE_INDEX)
            logger.info("✅ Pinecone vector store connected")
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone: {e}")
            self.index = None

    def _ensure_connected(self):
        if self.index is None:
            self.connect()

    def _embed(self, text: str) -> list:
        """Convert text to embedding vector with safe fallbacks."""
        if self.openai_embedder and settings.OPENAI_API_KEY != "mock-key":
            try:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                return loop.run_until_complete(self.openai_embedder.aembed_query(text))
            except Exception as e:
                logger.error(f"OpenAI embedding generation failed: {e}")

        # Default fallback: return zero vector of dimension 1536
        return [0.0] * 1536

    async def store_memory(self, user_id: str, category: str, key: str, value: dict) -> str:
        """Store a memory item as a vector + metadata."""
        self._ensure_connected()
        if not self.index:
            logger.warning("Pinecone vector store not connected. Skipping memory store.")
            return ""
        memory_text = f"{category}: {key} = {value}"
        vector = self._embed(memory_text)
        vector_id = str(uuid.uuid4())

        self.index.upsert(vectors=[{
            "id": vector_id,
            "values": vector,
            "metadata": {
                "user_id":  user_id,
                "category": category,
                "key":      key,
                "value":    str(value),
            }
        }])
        logger.info(f"Stored memory: [{category}] {key}")
        return vector_id

    async def search_memory(self, user_id: str, query: str, top_k: int = 5) -> list:
        """Semantic search through user's memory."""
        self._ensure_connected()
        if not self.index:
            logger.warning("Pinecone vector store not connected. Skipping semantic search.")
            return []
        vector = self._embed(query)
        results = self.index.query(
            vector=vector,
            top_k=top_k,
            filter={"user_id": {"$eq": user_id}},
            include_metadata=True,
        )
        memories = []
        for match in results.matches:
            memories.append({
                "score":    match.score,
                "category": match.metadata.get("category"),
                "key":      match.metadata.get("key"),
                "value":    match.metadata.get("value"),
            })
        return memories

    async def store_contact(self, user_id: str, alias: str, contact_data: dict) -> str:
        """Store a contact with alias — 'Amma', 'Anna', 'Ravi'."""
        return await self.store_memory(user_id, "contact", alias, contact_data)

    async def find_contact(self, user_id: str, name_or_alias: str) -> dict | None:
        """Find a contact by name or alias via semantic search."""
        results = await self.search_memory(user_id, f"contact {name_or_alias}", top_k=3)
        for r in results:
            if r["category"] == "contact" and r["score"] > 0.7:
                import ast
                try:
                    return ast.literal_eval(r["value"])
                except Exception:
                    return {"name": r["key"], "raw": r["value"]}
        return None


vector_store = VectorMemoryStore()
