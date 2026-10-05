from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.common.result import PageResult, Result
from app.core.deps import get_db, operation_log, require_admin
from app.models import User
from app.schemas import LogBatchDeleteRequest, SystemLogVO
from app.services import log_service

router = APIRouter(prefix="/logs", tags=["系统日志"])


@router.get("")
def page_logs(
    current: int = 1,
    size: int = 10,
    username: str | None = None,
    type: str = "login",
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Result[PageResult[SystemLogVO]]:
    return Result.ok(log_service.page_logs(db, current, size, username, type))


@router.delete("/batch")
@operation_log(module="系统日志", action="批量删除日志")
def delete_batch(
    body: LogBatchDeleteRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[None]:
    log_service.batch_delete(db, body.type, body.ids)
    return Result.ok()
