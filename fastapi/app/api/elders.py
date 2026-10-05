from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.common.result import PageResult, Result
from app.core.deps import get_current_user, get_db, operation_log, require_admin
from app.models import User
from app.schemas.elder import (
    ElderHealthVO,
    ElderSaveRequest,
    ElderVO,
    FamilyBindRequest,
    FamilyMemberVO,
    UserSelfBindRequest,
)
from app.services import elder_service

router = APIRouter(tags=["老人档案"])


@router.get("/elders")
def page_elders(
    current: int = 1,
    size: int = 10,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Result[PageResult[ElderVO]]:
    return Result.ok(elder_service.page_elders(db, current, size, keyword))


@router.get("/elders/{elder_id}")
def get_elder(
    elder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[ElderVO]:
    return Result.ok(elder_service.get_elder(db, elder_id, current_user))


@router.get("/elders/{elder_id}/health")
def get_health(
    elder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[ElderHealthVO]:
    return Result.ok(elder_service.get_health(db, elder_id, current_user))


@router.post("/elders")
@operation_log(module="老人档案", action="新增老人")
def create_elder(
    body: ElderSaveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[ElderVO]:
    return Result.ok(elder_service.create_elder(db, body))


@router.put("/elders/{elder_id}")
@operation_log(module="老人档案", action="修改老人")
def update_elder(
    elder_id: int,
    body: ElderSaveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[ElderVO]:
    return Result.ok(elder_service.update_elder(db, elder_id, body))


@router.delete("/elders/{elder_id}")
@operation_log(module="老人档案", action="删除老人")
def delete_elder(
    elder_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[None]:
    elder_service.delete_elder(db, elder_id)
    return Result.ok()


@router.get("/family/my-elders")
def my_elders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[list[ElderVO]]:
    return Result.ok(elder_service.my_elders(db, current_user))


@router.get("/family/bindings")
def my_bindings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[list[FamilyMemberVO]]:
    return Result.ok(elder_service.list_my_bindings(db, current_user))


@router.post("/family/bind")
@operation_log(module="家属绑定", action="自助绑定")
def self_bind_family(
    body: UserSelfBindRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[FamilyMemberVO]:
    return Result.ok(elder_service.self_bind_family(db, current_user, body))


@router.delete("/family/bindings/{bind_id}")
@operation_log(module="家属绑定", action="自助解绑")
def self_unbind_family(
    bind_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[None]:
    elder_service.unbind_family(db, bind_id, current_user)
    return Result.ok()


@router.get("/admin/family")
def list_family(
    elder_id: int | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Result[list[FamilyMemberVO]]:
    if elder_id is None:
        from app.common.exceptions import BusinessException

        raise BusinessException("请指定老人")
    return Result.ok(elder_service.list_family(db, elder_id))


@router.post("/admin/family")
@operation_log(module="家属绑定", action="绑定家属")
def bind_family(
    body: FamilyBindRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[FamilyMemberVO]:
    return Result.ok(elder_service.bind_family(db, body))


@router.delete("/admin/family/{bind_id}")
@operation_log(module="家属绑定", action="解绑家属")
def unbind_family(
    bind_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[None]:
    elder_service.unbind_family(db, bind_id, current_user)
    return Result.ok()
