import uuid
import logging
from typing import List, Optional, Dict, Any
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, SearchParams
from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Qdrant vector database wrapper for semantic search and retrieval."""

    def __init__(self):
        self.client = None
        self.collection_name = "academia"
        self.vector_size = settings.EMBEDDING_DIMENSION
        if settings.QDRANT_URL:
            self.client = AsyncQdrantClient(url=settings.QDRANT_URL)
        else:
            logger.warning("Qdrant URL not configured. Vector store disabled.")

    async def ensure_collection(self):
        if not self.client:
            logger.warning("Qdrant not configured, skipping ensure_collection")
            return
        try:
            collections = await self.client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)
            if not exists:
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created collection {self.collection_name}")
        except Exception as e:
            logger.error(f"Collection setup error: {e}")

    async def upsert(self, collection_name: str, point_id: str, vector: List[float], payload: dict):
        if not self.client:
            raise RuntimeError("Qdrant not configured")
        point = PointStruct(id=point_id, vector=vector, payload=payload)
        await self.client.upsert(collection_name=collection_name, points=[point])

    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7,
        filter_: Optional[dict] = None,
    ) -> List[dict]:
        if not self.client:
            return []
        results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=Filter(**filter_) if filter_ else None,
            search_params=SearchParams(hnsw_ef=128, exact=False),
        )
        return [
            {
                "id": str(r.id),
                "score": r.score,
                "content": r.payload.get("content", ""),
                "metadata": r.payload,
            }
            for r in results
        ]

    async def delete_points(self, point_ids: List[str]):
        if not self.client:
            return
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=point_ids,
        )

    async def count(self) -> int:
        if not self.client:
            return 0
        result = await self.client.count(collection_name=self.collection_name)
        return result.count


vector_store = VectorStore()