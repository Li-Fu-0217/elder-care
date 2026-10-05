from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.common.result import PageResult, Result
from app.core.deps import get_current_user, get_db, operation_log, require_admin
from app.models import User
from app.schemas.community import (
    ActivityRegisterRequest,
    ActivityRegistrationVO,
    ActivitySaveRequest,
    ActivityVO,
    EmergencyAlertCreateRequest,
    EmergencyAlertUpdateRequest,
    EmergencyAlertVO,
)
from app.services import community_service

router = APIRouter(tags=["社区活动与紧急告警"])


@router.get("/activities")
def list_activities(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Result[list[ActivityVO]]:
    return Result.ok(community_service.list_active_activities(db))


@router.get("/admin/activities")
def page_admin_activities(
    current: int = 1,
    size: int = 10,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Result[PageResult[ActivityVO]]:
    return Result.ok(community_service.page_activities(db, current, size, keyword=keyword))


@router.post("/admin/activities")
@operation_log(module="社区活动", action="发布活动")
def create_activity(
    body: ActivitySaveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[ActivityVO]:
    return Result.ok(community_service.save_activity(db, body))


@router.put("/admin/activities/{activity_id}")
@operation_log(module="社区活动", action="编辑活动")
def update_activity(
    activity_id: int,
    body: ActivitySaveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[ActivityVO]:
    return Result.ok(community_service.save_activity(db, body, activity_id))


@router.delete("/admin/activities/{activity_id}")
@operation_log(module="社区活动", action="删除活动")
def delete_activity(
    activity_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[None]:
    community_service.delete_activity(db, activity_id)
    return Result.ok()


@router.post("/activities/{activity_id}/register")
@operation_log(module="社区活动", action="报名活动")
def register_activity(
    activity_id: int,
    body: ActivityRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[ActivityRegistrationVO]:
    return Result.ok(
        community_service.register_activity(db, activity_id, body, current_user)
    )


@router.get("/activities/my-registrations")
def my_registrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[list[ActivityRegistrationVO]]:
    return Result.ok(community_service.my_registrations(db, current_user))


@router.get("/admin/activities/registrations")
def page_registrations(
    current: int = 1,
    size: int = 10,
    activity_id: int | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Result[PageResult[ActivityRegistrationVO]]:
    return Result.ok(
        community_service.page_registrations(db, current, size, activity_id)
    )


@router.post("/alerts/emergency")
@operation_log(module="紧急告警", action="触发告警")
def create_alert(
    body: EmergencyAlertCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[EmergencyAlertVO]:
    return Result.ok(community_service.create_alert(db, body, current_user))


@router.get("/alerts")
def list_alerts(
    current: int = 1,
    size: int = 10,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[PageResult[EmergencyAlertVO]]:
    return Result.ok(
        community_service.page_alerts(db, current, size, status, current_user)
    )


@router.get("/admin/alerts")
def page_admin_alerts(
    current: int = 1,
    size: int = 10,
    status: str | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Result[PageResult[EmergencyAlertVO]]:
    return Result.ok(community_service.page_alerts(db, current, size, status, None))


@router.put("/admin/alerts/{alert_id}")
@operation_log(module="紧急告警", action="处理告警")
def update_alert(
    alert_id: int,
    body: EmergencyAlertUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[EmergencyAlertVO]:
    return Result.ok(community_service.update_alert(db, alert_id, body))
