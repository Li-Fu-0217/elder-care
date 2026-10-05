from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.common.result import Result
from app.core.deps import get_current_user, get_db, operation_log
from app.models import User
from app.schemas import (
    AvatarBindRequest,
    ChangePasswordRequest,
    ProfileUpdateRequest,
    UserVO,
)
from app.services import file_service, user_service

router = APIRouter(prefix="/profile", tags=["个人中心"])


@router.put("")
@operation_log(module="个人中心", action="修改资料")
def update_profile(
    body: ProfileUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[UserVO]:
    return Result.ok(user_service.update_profile(db, current_user, body))


@router.put("/avatar")
@operation_log(module="个人中心", action="绑定头像")
def bind_avatar(
    body: AvatarBindRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[UserVO]:
    return Result.ok(
        user_service.bind_avatar(
            db,
            current_user,
            body.path,
            file_service.resolve_local_path,
            file_service.delete_local_file,
        )
    )


@router.put("/password")
@operation_log(module="个人中心", action="修改密码")
def change_password(
    body: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[None]:
    user_service.change_password(db, current_user, body)
    return Result.ok()
