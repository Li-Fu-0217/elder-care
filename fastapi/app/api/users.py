from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.common.result import PageResult, Result
from app.core.deps import get_db, operation_log, require_admin
from app.models import User
from app.schemas import UserSaveRequest, UserVO
from app.services import user_service

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("")
def page_users(
    current: int = 1,
    size: int = 10,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Result[PageResult[UserVO]]:
    return Result.ok(user_service.page_users(db, current, size, keyword))


@router.get("/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Result[UserVO]:
    return Result.ok(user_service.get_user_by_id(db, user_id))


@router.post("")
@operation_log(module="用户管理", action="新增用户")
def create_user(
    body: UserSaveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[UserVO]:
    return Result.ok(user_service.create_user(db, body))


@router.put("/{user_id}")
@operation_log(module="用户管理", action="修改用户")
def update_user(
    user_id: int,
    body: UserSaveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[UserVO]:
    return Result.ok(user_service.update_user(db, user_id, body))


@router.delete("/batch")
@operation_log(module="用户管理", action="批量删除用户")
def delete_users_batch(
    ids: list[int],
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[None]:
    user_service.delete_users(db, ids, current_user)
    return Result.ok()


@router.delete("/{user_id}")
@operation_log(module="用户管理", action="删除用户")
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[None]:
    user_service.delete_user(db, user_id, current_user)
    return Result.ok()
