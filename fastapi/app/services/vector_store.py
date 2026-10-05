"""Chroma 向量库封装：文档切片写入与 TopK 检索。"""

from __future__ import annotations

import threading
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings

_lock = threading.Lock()
_client: chromadb.PersistentClient | None = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection
    with _lock:
        if _collection is not None:
            return _collection
        settings = get_settings()
        path = settings.chroma_root
        path.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=str(path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        # 使用 Chroma 默认本地 Embedding（ONNX MiniLM），无需额外 API Key
        _collection = _client.get_or_create_collection(
            name=settings.knowledge_collection,
            metadata={"hnsw:space": "cosine"},
        )
        return _collection


def upsert_chunks(
    *,
    ids: list[str],
    documents: list[str],
    metadatas: list[dict[str, Any]],
) -> None:
    if not ids:
        return
    col = _get_collection()
    col.upsert(ids=ids, documents=documents, metadatas=metadatas)


def delete_by_document(document_id: int) -> None:
    col = _get_collection()
    try:
        col.delete(where={"document_id": {"$eq": int(document_id)}})
    except Exception:  # noqa: BLE001
        existing = col.get(include=[])
        ids = [
            i
            for i in (existing.get("ids") or [])
            if str(i).startswith(f"doc{document_id}-")
        ]
        if ids:
            col.delete(ids=ids)


def query_similar(question: str, top_k: int = 3) -> list[dict[str, Any]]:
    col = _get_collection()
    if col.count() == 0:
        return []
    result = col.query(
        query_texts=[question],
        n_results=min(top_k, max(col.count(), 1)),
        include=["documents", "metadatas", "distances"],
    )
    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    dists = (result.get("distances") or [[]])[0]
    ids = (result.get("ids") or [[]])[0]
    hits: list[dict[str, Any]] = []
    for i, content in enumerate(docs):
        meta = metas[i] if i < len(metas) else {}
        dist = dists[i] if i < len(dists) else None
        score = None if dist is None else max(0.0, 1.0 - float(dist))
        hits.append(
            {
                "embedding_id": ids[i] if i < len(ids) else None,
                "content": content,
                "metadata": meta or {},
                "score": score,
            }
        )
    return hits


def collection_count() -> int:
    return _get_collection().count()
