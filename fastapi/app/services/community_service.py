from datetime import datetime

from sqlmodel import Session, col, func, or_, select

from app.common.exceptions import BusinessException
from app.common.result import PageResult
from app.models import (
    ActivityRegistration,
    CommunityActivity,
    ElderProfile,
    EmergencyAlert,
    User,
)
from app.schemas.community import (
    ActivityRegisterRequest,
    ActivityRegistrationVO,
    ActivitySaveRequest,
    ActivityVO,
    EmergencyAlertCreateRequest,
    EmergencyAlertUpdateRequest,
    EmergencyAlertVO,
)
from app.services.elder_service import assert_family_access, list_bound_elder_ids


def _activity_to_vo(db: Session, row: CommunityActivity) -> ActivityVO:
    count = db.exec(
        select(func.count())
        .select_from(ActivityRegistration)
        .where(
            ActivityRegistration.activity_id == row.id,
            ActivityRegistration.status == "registered",
        )
    ).one()
    vo = ActivityVO.model_validate(row)
    vo.registered_count = count or 0
    return vo


def page_activities(
    db: Session,
    current: int,
    size: int,
    only_active: bool = False,
    keyword: str | None = None,
) -> PageResult[ActivityVO]:
    current = max(1, current)
    size = min(100, max(1, size))
    stmt = select(CommunityActivity)
    count_stmt = select(func.count()).select_from(CommunityActivity)
    if only_active:
        stmt = stmt.where(CommunityActivity.status == 1)
        count_stmt = count_stmt.where(CommunityActivity.status == 1)
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        cond = or_(
            col(CommunityActivity.title).like(kw),
            col(CommunityActivity.location).like(kw),
        )
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    total = db.exec(count_stmt).one()
    rows = db.exec(
        stmt.order_by(col(CommunityActivity.start_time).asc())
        .offset((current - 1) * size)
        .limit(size)
    ).all()
    return PageResult(
        records=[_activity_to_vo(db, r) for r in rows],
        total=total,
        current=current,
        size=size,
    )


def list_active_activities(db: Session) -> list[ActivityVO]:
    rows = db.exec(
        select(CommunityActivity)
        .where(CommunityActivity.status == 1)
        .order_by(col(CommunityActivity.start_time).asc())
    ).all()
    return [_activity_to_vo(db, r) for r in rows]


def save_activity(
    db: Session, body: ActivitySaveRequest, activity_id: int | None = None
) -> ActivityVO:
    now = datetime.now()
    if activity_id is None:
        row = CommunityActivity(**body.model_dump(), create_time=now, update_time=now)
        db.add(row)
    else:
        row = db.get(CommunityActivity, activity_id)
        if row is None:
            raise BusinessException("活动不存在")
        for k, v in body.model_dump().items():
            setattr(row, k, v)
        row.update_time = now
        db.add(row)
    db.commit()
    db.refresh(row)
    return _activity_to_vo(db, row)


def delete_activity(db: Session, activity_id: int) -> None:
    row = db.get(CommunityActivity, activity_id)
    if row is None:
        raise BusinessException("活动不存在")
    for reg in db.exec(
        select(ActivityRegistration).where(
            ActivityRegistration.activity_id == activity_id
        )
    ).all():
        db.delete(reg)
    db.delete(row)
    db.commit()


def register_activity(
    db: Session, activity_id: int, body: ActivityRegisterRequest, user: User
) -> ActivityRegistrationVO:
    activity = db.get(CommunityActivity, activity_id)
    if activity is None or activity.status != 1:
        raise BusinessException("活动不存在或已下架")
    assert_family_access(db, user, body.elder_id)
    if activity.capacity is not None:
        count = db.exec(
            select(func.count())
            .select_from(ActivityRegistration)
            .where(
                ActivityRegistration.activity_id == activity_id,
                ActivityRegistration.status == "registered",
            )
        ).one()
        if count >= activity.capacity:
            raise BusinessException("名额已满")
    exists = db.exec(
        select(ActivityRegistration).where(
            ActivityRegistration.activity_id == activity_id,
            ActivityRegistration.elder_id == body.elder_id,
        )
    ).first()
    now = datetime.now()
    if exists:
        if exists.status == "registered":
            raise BusinessException("已报名该活动")
        exists.status = "registered"
        exists.user_id = user.id
        exists.update_time = now
        db.add(exists)
        db.commit()
        db.refresh(exists)
        return _reg_to_vo(db, exists)
    row = ActivityRegistration(
        activity_id=activity_id,
        elder_id=body.elder_id,
        user_id=user.id,
        status="registered",
        create_time=now,
        update_time=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _reg_to_vo(db, row)


def cancel_registration(db: Session, reg_id: int, user: User) -> None:
    row = db.get(ActivityRegistration, reg_id)
    if row is None:
        raise BusinessException("报名记录不存在")
    if user.role != "ADMIN":
        assert_family_access(db, user, row.elder_id)
    row.status = "cancelled"
    row.update_time = datetime.now()
    db.add(row)
    db.commit()


def page_registrations(
    db: Session, current: int, size: int, activity_id: int | None = None
) -> PageResult[ActivityRegistrationVO]:
    current = max(1, current)
    size = min(100, max(1, size))
    stmt = select(ActivityRegistration)
    count_stmt = select(func.count()).select_from(ActivityRegistration)
    if activity_id is not None:
        stmt = stmt.where(ActivityRegistration.activity_id == activity_id)
        count_stmt = count_stmt.where(ActivityRegistration.activity_id == activity_id)
    total = db.exec(count_stmt).one()
    rows = db.exec(
        stmt.order_by(col(ActivityRegistration.id).desc())
        .offset((current - 1) * size)
        .limit(size)
    ).all()
    return PageResult(
        records=[_reg_to_vo(db, r) for r in rows],
        total=total,
        current=current,
        size=size,
    )


def my_registrations(db: Session, user: User) -> list[ActivityRegistrationVO]:
    ids = list_bound_elder_ids(db, user.id or 0)
    if not ids:
        return []
    rows = db.exec(
        select(ActivityRegistration)
        .where(
            col(ActivityRegistration.elder_id).in_(ids),
            ActivityRegistration.status == "registered",
        )
        .order_by(col(ActivityRegistration.id).desc())
    ).all()
    return [_reg_to_vo(db, r) for r in rows]


def _reg_to_vo(db: Session, row: ActivityRegistration) -> ActivityRegistrationVO:
    activity = db.get(CommunityActivity, row.activity_id)
    elder = db.get(ElderProfile, row.elder_id)
    return ActivityRegistrationVO(
        id=row.id or 0,
        activity_id=row.activity_id,
        elder_id=row.elder_id,
        user_id=row.user_id,
        status=row.status,
        activity_title=activity.title if activity else None,
        elder_name=elder.name if elder else None,
        create_time=row.create_time,
    )


def create_alert(
    db: Session,
    body: EmergencyAlertCreateRequest,
    user: User,
    source: str = "manual",
) -> EmergencyAlertVO:
    assert_family_access(db, user, body.elder_id)
    now = datetime.now()
    row = EmergencyAlert(
        elder_id=body.elder_id,
        location=body.location,
        message=body.message or "紧急求助",
        status="open",
        notify_family=1,
        notify_staff=1,
        source=source,
        create_time=now,
        update_time=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    from app.services import notify_service

    elder = db.get(ElderProfile, body.elder_id)
    elder_name = elder.name if elder else f"老人#{body.elder_id}"
    loc = f"；位置：{body.location}" if body.location else ""
    notify_service.notify_family_members(
        db,
        elder_id=body.elder_id,
        title=f"紧急求助：{elder_name}",
        content=f"{elder_name}触发紧急求助。{row.message or ''}{loc}请尽快关注并联系社区。",
        msg_type="emergency",
        source=source if source in ("agent", "manual") else "system",
        related_id=row.id,
    )
    return _alert_to_vo(db, row)


def page_alerts(
    db: Session,
    current: int,
    size: int,
    status: str | None = None,
    user: User | None = None,
) -> PageResult[EmergencyAlertVO]:
    current = max(1, current)
    size = min(100, max(1, size))
    stmt = select(EmergencyAlert)
    count_stmt = select(func.count()).select_from(EmergencyAlert)
    if user is not None and user.role != "ADMIN":
        ids = list_bound_elder_ids(db, user.id or 0)
        if not ids:
            return PageResult(records=[], total=0, current=current, size=size)
        stmt = stmt.where(col(EmergencyAlert.elder_id).in_(ids))
        count_stmt = count_stmt.where(col(EmergencyAlert.elder_id).in_(ids))
    if status:
        stmt = stmt.where(EmergencyAlert.status == status)
        count_stmt = count_stmt.where(EmergencyAlert.status == status)
    total = db.exec(count_stmt).one()
    rows = db.exec(
        stmt.order_by(col(EmergencyAlert.id).desc())
        .offset((current - 1) * size)
        .limit(size)
    ).all()
    return PageResult(
        records=[_alert_to_vo(db, r) for r in rows],
        total=total,
        current=current,
        size=size,
    )


def update_alert(
    db: Session, alert_id: int, body: EmergencyAlertUpdateRequest
) -> EmergencyAlertVO:
    row = db.get(EmergencyAlert, alert_id)
    if row is None:
        raise BusinessException("告警不存在")
    if body.status not in ("open", "handling", "closed"):
        raise BusinessException("状态无效")
    row.status = body.status
    if body.notify_family is not None:
        row.notify_family = body.notify_family
    if body.notify_staff is not None:
        row.notify_staff = body.notify_staff
    row.update_time = datetime.now()
    db.add(row)
    db.commit()
    db.refresh(row)
    return _alert_to_vo(db, row)


def _alert_to_vo(db: Session, row: EmergencyAlert) -> EmergencyAlertVO:
    elder = db.get(ElderProfile, row.elder_id)
    return EmergencyAlertVO(
        id=row.id or 0,
        elder_id=row.elder_id,
        location=row.location,
        message=row.message,
        status=row.status,
        notify_family=row.notify_family,
        notify_staff=row.notify_staff,
        source=row.source,
        elder_name=elder.name if elder else None,
        create_time=row.create_time,
        update_time=row.update_time,
    )
