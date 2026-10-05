from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlmodel import Session

from app.common.result import PageResult, Result
from app.core.deps import get_current_user, get_db, operation_log, require_admin
from app.models import User
from app.schemas.knowledge import (
    KnowledgeChunkVO,
    KnowledgeDocumentVO,
    KnowledgeQueryRequest,
    KnowledgeQueryVO,
)
from app.services import knowledge_service

router = APIRouter(tags=["知识库 RAG"])


@router.get("/admin/knowledge/documents")
def page_documents(
    current: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Result[PageResult[KnowledgeDocumentVO]]:
    return Result.ok(knowledge_service.page_documents(db, current, size))


@router.get("/admin/knowledge/documents/{document_id}/chunks")
def list_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Result[list[KnowledgeChunkVO]]:
    return Result.ok(knowledge_service.list_chunks(db, document_id))


@router.post("/admin/knowledge/documents")
@operation_log(module="知识库", action="上传文档")
async def upload_document(
    request: Request,
    title: str = Form(""),
    doc_type: str = Form("policy"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[KnowledgeDocumentVO]:
    raw = await file.read()
    if not raw:
        from app.common.exceptions import BusinessException

        raise BusinessException("文件为空", code=400)
    vo = knowledge_service.upload_and_index(
        db,
        title=title.strip() or (file.filename or "未命名文档"),
        doc_type=doc_type.strip() or "policy",
        filename=file.filename or "upload.txt",
        raw=raw,
    )
    return Result.ok(vo)


@router.delete("/admin/knowledge/documents/{document_id}")
@operation_log(module="知识库", action="删除文档")
def delete_document(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[None]:
    knowledge_service.delete_document(db, document_id)
    return Result.ok()


@router.post("/knowledge/query")
def query_knowledge(
    body: KnowledgeQueryRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Result[KnowledgeQueryVO]:
    return Result.ok(
        knowledge_service.query_knowledge(db, body.question, body.top_k)
    )
