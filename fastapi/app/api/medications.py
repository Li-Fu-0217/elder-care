from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.common.result import PageResult, Result
from app.core.deps import get_current_user, get_db, operation_log, require_admin
from app.models import User
from app.schemas.elder import (
    MedicationLogVO,
    MedicationScheduleSaveRequest,
    MedicationScheduleVO,
)
from app.services import elder_service

router = APIRouter(tags=["用药管理"])


@router.get("/medications/schedules")
def list_or_page_schedules(
    elder_id: int | None = None,
    current: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result:
    if current_user.role == "ADMIN":
        return Result.ok(
            elder_service.page_schedules(db, current, size, elder_id)
        )
    if elder_id is None:
        from app.common.exceptions import BusinessException

        raise BusinessException("请指定老人")
    return Result.ok(
        elder_service.list_schedules_for_elder(db, elder_id, current_user)
    )


@router.post("/admin/medications/schedules")
@operation_log(module="用药管理", action="新增用药计划")
def create_schedule(
    body: MedicationScheduleSaveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[MedicationScheduleVO]:
    return Result.ok(elder_service.create_schedule(db, body))


@router.put("/admin/medications/schedules/{schedule_id}")
@operation_log(module="用药管理", action="修改用药计划")
def update_schedule(
    schedule_id: int,
    body: MedicationScheduleSaveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[MedicationScheduleVO]:
    return Result.ok(elder_service.update_schedule(db, schedule_id, body))


@router.delete("/admin/medications/schedules/{schedule_id}")
@operation_log(module="用药管理", action="删除用药计划")
def delete_schedule(
    schedule_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[None]:
    elder_service.delete_schedule(db, schedule_id)
    return Result.ok()


@router.get("/medications/logs")
def page_logs(
    current: int = 1,
    size: int = 10,
    elder_id: int | None = None,
    status: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[PageResult[MedicationLogVO]]:
    return Result.ok(
        elder_service.page_medication_logs(
            db, current, size, elder_id, status, current_user
        )
    )


@router.post("/medications/logs/{log_id}/taken")
@operation_log(module="用药管理", action="标记已服用")
def mark_taken(
    log_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[MedicationLogVO]:
    return Result.ok(elder_service.mark_taken(db, log_id, current_user))
