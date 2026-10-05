from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.common.result import PageResult, Result
from app.core.deps import get_current_user, get_db
from app.models import User
from app.schemas.notify import NotifyInboxVO, UnreadCountVO
from app.services import notify_service

router = APIRouter(tags=["站内消息"])


@router.get("/notifications")
def list_notifications(
    current: int = 1,
    size: int = 10,
    is_read: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[PageResult[NotifyInboxVO]]:
    return Result.ok(
        notify_service.page_my_notifications(db, current_user, current, size, is_read)
    )


@router.get("/notifications/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[UnreadCountVO]:
    return Result.ok(notify_service.unread_count(db, current_user))


@router.put("/notifications/{notify_id}/read")
def read_one(
    notify_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[NotifyInboxVO]:
    return Result.ok(notify_service.mark_read(db, current_user, notify_id))


@router.put("/notifications/read-all")
def read_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[UnreadCountVO]:
    return Result.ok(notify_service.mark_all_read(db, current_user))
