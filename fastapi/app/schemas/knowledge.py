from datetime import datetime
from typing import Optional

from pydantic import Field

from app.common.result import CamelModel


class KnowledgeDocumentVO(CamelModel):
    id: int
    title: str
    file_path: Optional[str] = None
    doc_type: Optional[str] = None
    status: int
    chunk_count: int = 0
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class KnowledgeChunkVO(CamelModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    embedding_id: Optional[str] = None
    create_time: Optional[datetime] = None


class KnowledgeQueryRequest(CamelModel):
    question: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=3, ge=1, le=10)


class KnowledgeChunkHitVO(CamelModel):
    chunk_id: int
    document_id: int
    document_title: Optional[str] = None
    doc_type: Optional[str] = None
    content: str
    score: Optional[float] = None


class KnowledgeQueryVO(CamelModel):
    question: str
    hits: list[KnowledgeChunkHitVO]
    answer_hint: Optional[str] = None
