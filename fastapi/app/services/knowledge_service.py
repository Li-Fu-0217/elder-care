"""知识库：上传切片、Chroma 向量化、检索。"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session, col, func, select

from app.common.exceptions import BusinessException
from app.common.result import PageResult
from app.core.config import get_settings
from app.models import KnowledgeChunk, KnowledgeDocument
from app.schemas.knowledge import (
    KnowledgeChunkHitVO,
    KnowledgeChunkVO,
    KnowledgeDocumentVO,
    KnowledgeQueryVO,
)
from app.services import vector_store

_CHUNK_SIZE = 280
_CHUNK_OVERLAP = 40


def page_documents(
    db: Session, current: int, size: int
) -> PageResult[KnowledgeDocumentVO]:
    total = db.exec(select(func.count()).select_from(KnowledgeDocument)).one()
    rows = db.exec(
        select(KnowledgeDocument)
        .order_by(col(KnowledgeDocument.id).desc())
        .offset((current - 1) * size)
        .limit(size)
    ).all()
    vos: list[KnowledgeDocumentVO] = []
    for d in rows:
        cnt = db.exec(
            select(func.count())
            .select_from(KnowledgeChunk)
            .where(KnowledgeChunk.document_id == d.id)
        ).one()
        vos.append(_to_doc_vo(d, int(cnt or 0)))
    return PageResult(records=vos, total=int(total or 0), current=current, size=size)


def upload_and_index(
    db: Session,
    *,
    title: str,
    doc_type: str | None,
    filename: str,
    raw: bytes,
) -> KnowledgeDocumentVO:
    text = _extract_text(filename, raw)
    if not text.strip():
        raise BusinessException("未能从文件中提取有效文本，请上传 txt/md/pdf", code=400)

    settings = get_settings()
    now = datetime.now()
    rel_dir = Path("knowledge")
    abs_dir = settings.upload_root / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w.\u4e00-\u9fff-]+", "_", filename)[:80]
    stamp = now.strftime("%Y%m%d%H%M%S")
    rel_path = str(rel_dir / f"{stamp}_{safe_name}").replace("\\", "/")
    (settings.upload_root / rel_path).write_bytes(raw)

    doc = KnowledgeDocument(
        title=(title or Path(filename).stem)[:200],
        file_path=rel_path,
        doc_type=(doc_type or "policy")[:50],
        status=0,
        create_time=now,
        update_time=now,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        chunks = _split_text(text)
        _persist_chunks(db, doc, chunks)
        doc.status = 1
        doc.update_time = datetime.now()
        db.add(doc)
        db.commit()
        db.refresh(doc)
    except Exception as exc:  # noqa: BLE001
        doc.status = 0
        doc.update_time = datetime.now()
        db.add(doc)
        db.commit()
        raise BusinessException(f"向量化失败：{exc}", code=500) from exc

    cnt = len(chunks)
    return _to_doc_vo(doc, cnt)


def delete_document(db: Session, document_id: int) -> None:
    doc = db.get(KnowledgeDocument, document_id)
    if not doc:
        raise BusinessException("文档不存在", code=404)
    chunks = db.exec(
        select(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id)
    ).all()
    for c in chunks:
        db.delete(c)
    vector_store.delete_by_document(document_id)
    if doc.file_path and not str(doc.file_path).startswith("seed/"):
        path = get_settings().upload_root / doc.file_path
        if path.is_file():
            try:
                path.unlink()
            except OSError:
                pass
    db.delete(doc)
    db.commit()


def list_chunks(db: Session, document_id: int) -> list[KnowledgeChunkVO]:
    doc = db.get(KnowledgeDocument, document_id)
    if not doc:
        raise BusinessException("文档不存在", code=404)
    rows = db.exec(
        select(KnowledgeChunk)
        .where(KnowledgeChunk.document_id == document_id)
        .order_by(col(KnowledgeChunk.chunk_index).asc())
    ).all()
    return [
        KnowledgeChunkVO(
            id=int(r.id or 0),
            document_id=r.document_id,
            chunk_index=r.chunk_index,
            content=r.content,
            embedding_id=r.embedding_id,
            create_time=r.create_time,
        )
        for r in rows
    ]


def ensure_vector_index(db: Session) -> int:
    """将 MySQL 中已就绪切片同步到 Chroma（种子/重启后）。"""
    chunks = db.exec(select(KnowledgeChunk)).all()
    if not chunks:
        return 0
    # 数量不一致时全量 upsert（新增种子后可自动补齐向量）
    if vector_store.collection_count() == len(chunks):
        return vector_store.collection_count()

    docs = {
        d.id: d
        for d in db.exec(select(KnowledgeDocument)).all()
        if d.id is not None
    }
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []
    for c in chunks:
        eid = c.embedding_id or f"doc{c.document_id}-c{c.chunk_index}"
        doc = docs.get(c.document_id)
        ids.append(eid)
        documents.append(c.content)
        metadatas.append(
            {
                "document_id": int(c.document_id),
                "chunk_id": int(c.id or 0),
                "chunk_index": int(c.chunk_index),
                "title": (doc.title if doc else "")[:200],
                "doc_type": (doc.doc_type if doc and doc.doc_type else "")[:50],
            }
        )
    vector_store.upsert_chunks(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)


def query_knowledge(
    db: Session, question: str, top_k: int = 3
) -> KnowledgeQueryVO:
    ensure_vector_index(db)
    vec_hits = vector_store.query_similar(question, top_k=max(top_k, 5))
    kw_hits = _keyword_search(db, question, top_k=max(top_k, 5))

    merged: dict[int, dict[str, Any]] = {}
    for h in vec_hits:
        meta = h.get("metadata") or {}
        cid = int(meta.get("chunk_id") or 0)
        key = cid or hash(h.get("content") or "")
        merged[key] = {
            "content": h.get("content") or "",
            "score": float(h.get("score") or 0) * 0.6,
            "metadata": meta,
        }
    for h in kw_hits:
        meta = h.get("metadata") or {}
        cid = int(meta.get("chunk_id") or 0)
        key = cid or hash(h.get("content") or "")
        prev = merged.get(key)
        kw_score = float(h.get("score") or 0)
        if prev:
            prev["score"] = prev["score"] + kw_score * 1.2
        else:
            merged[key] = {
                "content": h.get("content") or "",
                "score": kw_score * 1.2,
                "metadata": meta,
            }

    ranked = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
    if not ranked:
        ranked = vec_hits or kw_hits

    hits: list[KnowledgeChunkHitVO] = []
    for h in ranked[:top_k]:
        meta = h.get("metadata") or {}
        chunk_id = int(meta.get("chunk_id") or 0)
        document_id = int(meta.get("document_id") or 0)
        content = h.get("content") or ""
        if not chunk_id and content:
            row = db.exec(
                select(KnowledgeChunk).where(KnowledgeChunk.content == content)
            ).first()
            if row:
                chunk_id = int(row.id or 0)
                document_id = int(row.document_id)
        doc = db.get(KnowledgeDocument, document_id) if document_id else None
        hits.append(
            KnowledgeChunkHitVO(
                chunk_id=chunk_id,
                document_id=document_id,
                document_title=doc.title if doc else meta.get("title"),
                doc_type=doc.doc_type if doc else meta.get("doc_type"),
                content=content,
                score=h.get("score"),
            )
        )

    hint = None
    if hits:
        joined = "\n".join(f"- {x.content}" for x in hits[:3])
        hint = f"根据知识库检索，可参考：\n{joined}"
    return KnowledgeQueryVO(question=question, hits=hits, answer_hint=hint)


def _keyword_search(db: Session, question: str, top_k: int) -> list[dict[str, Any]]:
    # 中文：按标点切分 + 提取 2～4 字片段，提高命中率
    parts = [t for t in re.split(r"[\s，。？?、；;！!：:]+", question) if len(t) >= 2]
    tokens: list[str] = []
    for p in parts:
        tokens.append(p)
        if len(p) >= 4:
            for n in (2, 3, 4):
                for i in range(0, len(p) - n + 1):
                    tokens.append(p[i : i + n])
    # 去重保序
    seen: set[str] = set()
    uniq: list[str] = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    tokens = uniq[:40]
    if not tokens and question:
        tokens = [question[:8]]

    scored: list[tuple[float, KnowledgeChunk]] = []
    all_chunks = db.exec(select(KnowledgeChunk)).all()
    for c in all_chunks:
        score = 0.0
        for t in tokens:
            if t in c.content:
                # 更长短语权重更高
                score += min(len(t), 6) * 0.35
        if score > 0:
            scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    out: list[dict[str, Any]] = []
    for score, c in scored[:top_k]:
        doc = db.get(KnowledgeDocument, c.document_id)
        out.append(
            {
                "content": c.content,
                "score": score,
                "metadata": {
                    "chunk_id": c.id,
                    "document_id": c.document_id,
                    "title": doc.title if doc else "",
                    "doc_type": doc.doc_type if doc else "",
                },
            }
        )
    return out


def _persist_chunks(db: Session, doc: KnowledgeDocument, chunks: list[str]) -> None:
    assert doc.id is not None
    # 清旧切片
    old = db.exec(
        select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc.id)
    ).all()
    for o in old:
        db.delete(o)
    db.commit()
    vector_store.delete_by_document(doc.id)

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []
    now = datetime.now()
    for i, text in enumerate(chunks):
        eid = f"doc{doc.id}-c{i}"
        row = KnowledgeChunk(
            document_id=doc.id,
            chunk_index=i,
            content=text,
            embedding_id=eid,
            create_time=now,
        )
        db.add(row)
        db.flush()
        ids.append(eid)
        documents.append(text)
        metadatas.append(
            {
                "document_id": int(doc.id),
                "chunk_id": int(row.id or 0),
                "chunk_index": i,
                "title": doc.title[:200],
                "doc_type": (doc.doc_type or "")[:50],
            }
        )
    db.commit()
    vector_store.upsert_chunks(ids=ids, documents=documents, metadatas=metadatas)


def _split_text(text: str) -> list[str]:
    cleaned = re.sub(r"\r\n?", "\n", text).strip()
    if not cleaned:
        return []
    # 按段落优先
    parts = [p.strip() for p in re.split(r"\n{2,}", cleaned) if p.strip()]
    if not parts:
        parts = [cleaned]
    chunks: list[str] = []
    buf = ""
    for p in parts:
        if len(p) <= _CHUNK_SIZE:
            if buf and len(buf) + len(p) + 1 > _CHUNK_SIZE:
                chunks.append(buf)
                buf = p
            else:
                buf = f"{buf}\n{p}".strip() if buf else p
        else:
            if buf:
                chunks.append(buf)
                buf = ""
            start = 0
            while start < len(p):
                end = min(start + _CHUNK_SIZE, len(p))
                chunks.append(p[start:end])
                if end >= len(p):
                    break
                start = max(end - _CHUNK_OVERLAP, start + 1)
    if buf:
        chunks.append(buf)
    return chunks


def _extract_text(filename: str, raw: bytes) -> str:
    lower = filename.lower()
    if lower.endswith((".txt", ".md", ".markdown")):
        for enc in ("utf-8", "gbk", "utf-16"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="ignore")
    if lower.endswith(".pdf"):
        try:
            from io import BytesIO

            from pypdf import PdfReader

            reader = PdfReader(BytesIO(raw))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception as exc:  # noqa: BLE001
            raise BusinessException(f"PDF 解析失败：{exc}", code=400) from exc
    raise BusinessException("仅支持 txt / md / pdf 文件", code=400)


def _to_doc_vo(doc: KnowledgeDocument, chunk_count: int) -> KnowledgeDocumentVO:
    return KnowledgeDocumentVO(
        id=int(doc.id or 0),
        title=doc.title,
        file_path=doc.file_path,
        doc_type=doc.doc_type,
        status=doc.status,
        chunk_count=chunk_count,
        create_time=doc.create_time,
        update_time=doc.update_time,
    )
