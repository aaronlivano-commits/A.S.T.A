"""ChromaDB-backed vector store for topic retrieval (RAG)."""
from __future__ import annotations

import logging
import os
from typing import Any, List, Optional

from ..config import get_settings

logger = logging.getLogger(__name__)


def _import_chroma() -> Any:
    """Lazy import so the rest of the app boots even if chromadb is missing
    or the local sqlite3 is too old for its compiled wheels."""
    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "chromadb is not installed. Run: pip install chromadb"
        ) from exc
    return chromadb, ChromaSettings


class VectorStore:
    """One persistent collection per topic, identified by topic_id."""

    def __init__(self, persist_dir: Optional[str] = None) -> None:
        settings = get_settings()
        self._persist_dir = persist_dir or settings.chroma_persist_dir
        os.makedirs(self._persist_dir, exist_ok=True)
        chromadb, ChromaSettings = _import_chroma()
        self._client = chromadb.PersistentClient(
            path=self._persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def _collection_name(self, topic_id: str) -> str:
        prefix = get_settings().collection_prefix
        return f"{prefix}{topic_id}"

    def get_or_create(self, topic_id: str):
        return self._client.get_or_create_collection(
            name=self._collection_name(topic_id),
            metadata={"hnsw:space": "cosine"},
        )

    def add(
        self,
        topic_id: str,
        *,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
    ) -> int:
        if not documents:
            return 0
        collection = self.get_or_create(topic_id)
        kwargs = {
            "documents": documents,
            "embeddings": embeddings,
        }
        if metadatas:
            kwargs["metadatas"] = metadatas
        if ids:
            kwargs["ids"] = ids
        else:
            kwargs["ids"] = [f"chunk_{i}" for i in range(len(documents))]
        collection.add(**kwargs)
        return len(documents)

    def query(
        self,
        topic_id: str,
        *,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[dict]:
        collection = self.get_or_create(topic_id)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        out: List[dict] = []
        for i, doc in enumerate(results.get("documents", [[]])[0]):
            entry = {"text": doc}
            if results.get("metadatas"):
                entry["metadata"] = results["metadatas"][0][i]
            if results.get("distances"):
                entry["distance"] = results["distances"][0][i]
            out.append(entry)
        return out

    def count(self, topic_id: str) -> int:
        return self.get_or_create(topic_id).count()

    def delete_topic(self, topic_id: str) -> None:
        try:
            self._client.delete_collection(self._collection_name(topic_id))
        except Exception as exc:  # noqa: BLE001
            logger.warning("delete_collection failed for %s: %s", topic_id, exc)
