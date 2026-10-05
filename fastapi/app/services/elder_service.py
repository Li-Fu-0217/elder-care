"""老人档案、家属绑定、用药、服务预约等核心业务。

权限约定：USER 仅能操作已绑定老人；ADMIN 可管理全部档案与计划。
预约防重：slot_lock 唯一约束 + version 乐观锁（不做 Redis）。
"""

from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, func, or_, select

from app.common.exceptions import BusinessException
from app.common.result import PageResult
from app.models import (
    ElderProfile,
    FamilyMember,
    MedicationLog,
    MedicationSchedule,
    ServiceBooking,
    ServiceCatalog,
    User,
)
from app.schemas.elder import (
    CareDashboardVO,
    ElderHealthVO,
    ElderSaveRequest,
    ElderVO,
    FamilyBindRequest,
    FamilyMemberVO,
    MedicationLogVO,
    MedicationScheduleSaveRequest,
    MedicationScheduleVO,
    ServiceBookingCreateRequest,
    ServiceBookingUpdateRequest,
    ServiceBookingVO,
    ServiceCatalogSaveRequest,
    ServiceCatalogVO,
    ServiceSlotsVO,
    UserSelfBindRequest,
)


def elder_to_vo(row: ElderProfile) -> ElderVO:
    return ElderVO.model_validate(row)


def assert_family_access(db: Session, user: User, elder_id: int) -> ElderProfile:
    """校验当前用户可否访问该老人；管理员放行，子女须已绑定。"""
    elder = db.get(ElderProfile, elder_id)
    if elder is None:
        raise BusinessException("老人档案不存在")
    if user.role == "ADMIN":
        return elder
    link = db.exec(
        select(FamilyMember).where(
            FamilyMember.user_id == user.id,
            FamilyMember.elder_id == elder_id,
        )
    ).first()
    if link is None:
        raise BusinessException("无权访问该老人档案", code=403)
    return elder


def list_bound_elder_ids(db: Session, user_id: int) -> list[int]:
    """返回子女账号已绑定的老人 ID 列表。"""
    rows = db.exec(
        select(FamilyMember.elder_id).where(FamilyMember.user_id == user_id)
    ).all()
    return list(rows)


def page_elders(
    db: Session, current: int, size: int, keyword: str | None
) -> PageResult[ElderVO]:
    current = max(1, current)
    size = min(100, max(1, size))
    stmt = select(ElderProfile)
    count_stmt = select(func.count()).select_from(ElderProfile)
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        cond = or_(
            col(ElderProfile.name).like(kw),
            col(ElderProfile.phone).like(kw),
        )
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    total = db.exec(count_stmt).one()
    rows = db.exec(
        stmt.order_by(col(ElderProfile.id).desc())
        .offset((current - 1) * size)
        .limit(size)
    ).all()
    return PageResult(
        records=[elder_to_vo(r) for r in rows],
        total=total,
        current=current,
        size=size,
    )


def get_elder(db: Session, elder_id: int, user: User) -> ElderVO:
    elder = assert_family_access(db, user, elder_id)
    return elder_to_vo(elder)


def create_elder(db: Session, body: ElderSaveRequest) -> ElderVO:
    now = datetime.now()
    row = ElderProfile(
        **body.model_dump(),
        create_time=now,
        update_time=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return elder_to_vo(row)


def update_elder(db: Session, elder_id: int, body: ElderSaveRequest) -> ElderVO:
    row = db.get(ElderProfile, elder_id)
    if row is None:
        raise BusinessException("老人档案不存在")
    for k, v in body.model_dump().items():
        setattr(row, k, v)
    row.update_time = datetime.now()
    db.add(row)
    db.commit()
    db.refresh(row)
    return elder_to_vo(row)


def delete_elder(db: Session, elder_id: int) -> None:
    row = db.get(ElderProfile, elder_id)
    if row is None:
        raise BusinessException("老人档案不存在")
    active = db.exec(
        select(func.count())
        .select_from(ServiceBooking)
        .where(
            ServiceBooking.elder_id == elder_id,
            col(ServiceBooking.status).in_(["pending", "confirmed"]),
        )
    ).one()
    if active:
        raise BusinessException("存在未完成预约，无法删除")
    for fm in db.exec(
        select(FamilyMember).where(FamilyMember.elder_id == elder_id)
    ).all():
        db.delete(fm)
    db.delete(row)
    db.commit()


def get_health(db: Session, elder_id: int, user: User) -> ElderHealthVO:
    elder = assert_family_access(db, user, elder_id)
    since = datetime.now() - timedelta(days=3)
    logs = db.exec(
        select(MedicationLog)
        .where(
            MedicationLog.elder_id == elder_id,
            MedicationLog.status == 0,
            MedicationLog.planned_time >= since,
        )
        .order_by(col(MedicationLog.planned_time).desc())
    ).all()
    log_vos = [_medication_log_to_vo(db, x) for x in logs]
    return ElderHealthVO(
        elder_id=elder.id or 0,
        name=elder.name,
        chronic_diseases=elder.chronic_diseases,
        current_medications=elder.current_medications,
        health_summary=elder.health_summary,
        recent_missed_count=len(log_vos),
        recent_missed_logs=log_vos,
    )


def my_elders(db: Session, user: User) -> list[ElderVO]:
    ids = list_bound_elder_ids(db, user.id or 0)
    if not ids:
        return []
    rows = db.exec(
        select(ElderProfile)
        .where(col(ElderProfile.id).in_(ids), ElderProfile.status == 1)
        .order_by(col(ElderProfile.id).asc())
    ).all()
    return [elder_to_vo(r) for r in rows]


def list_family(
    db: Session, elder_id: int | None = None
) -> list[FamilyMemberVO]:
    stmt = select(FamilyMember)
    if elder_id is not None:
        stmt = stmt.where(FamilyMember.elder_id == elder_id)
    rows = db.exec(stmt.order_by(col(FamilyMember.id).desc())).all()
    return [_family_to_vo(db, r) for r in rows]


def bind_family(db: Session, body: FamilyBindRequest) -> FamilyMemberVO:
    """绑定子女与老人；每位老人仅允许一位家属。"""
    user_id = body.user_id
    username = (body.username or "").strip()
    if user_id is None and username:
        user = db.exec(select(User).where(User.username == username)).first()
        if user is None:
            raise BusinessException("用户不存在")
        user_id = user.id
    if user_id is None or db.get(User, user_id) is None:
        raise BusinessException("请填写子女账号")
    if db.get(ElderProfile, body.elder_id) is None:
        raise BusinessException("老人档案不存在")
    # 每位老人仅允许绑定一位家属
    elder_bound = db.exec(
        select(FamilyMember).where(FamilyMember.elder_id == body.elder_id)
    ).first()
    if elder_bound and elder_bound.user_id != user_id:
        raise BusinessException("该老人已绑定一位家属，请先解绑后再更换")
    exists = db.exec(
        select(FamilyMember).where(
            FamilyMember.user_id == user_id,
            FamilyMember.elder_id == body.elder_id,
        )
    ).first()
    if exists:
        raise BusinessException("该家属已绑定此老人")
    now = datetime.now()
    row = FamilyMember(
        user_id=user_id,
        elder_id=body.elder_id,
        relation=body.relation,
        is_primary=body.is_primary if body.is_primary else 1,
        create_time=now,
        update_time=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _family_to_vo(db, row)


def self_bind_family(
    db: Session, user: User, body: UserSelfBindRequest
) -> FamilyMemberVO:
    """前台自助绑定：姓名+手机号须与档案一致。"""
    name = (body.elder_name or "").strip()
    phone = (body.elder_phone or "").strip()
    if not name or not phone:
        raise BusinessException("请填写老人姓名与手机号")
    elder = db.exec(
        select(ElderProfile).where(
            ElderProfile.name == name,
            ElderProfile.phone == phone,
            ElderProfile.status == 1,
        )
    ).first()
    if elder is None:
        raise BusinessException("未找到匹配的老人档案，请核对姓名与手机号")
    return bind_family(
        db,
        FamilyBindRequest(
            user_id=user.id or 0,
            elder_id=elder.id or 0,
            relation=body.relation or "家属",
            is_primary=body.is_primary,
        ),
    )


def list_my_bindings(db: Session, user: User) -> list[FamilyMemberVO]:
    rows = db.exec(
        select(FamilyMember)
        .where(FamilyMember.user_id == user.id)
        .order_by(col(FamilyMember.id).desc())
    ).all()
    return [_family_to_vo(db, r) for r in rows]


def unbind_family(db: Session, bind_id: int, user: User | None = None) -> None:
    row = db.get(FamilyMember, bind_id)
    if row is None:
        raise BusinessException("绑定记录不存在")
    if user is not None and user.role != "ADMIN":
        if row.user_id != user.id:
            raise BusinessException("只能解绑自己的家属关系", code=403)
    db.delete(row)
    db.commit()


def _family_to_vo(db: Session, row: FamilyMember) -> FamilyMemberVO:
    user = db.get(User, row.user_id)
    elder = db.get(ElderProfile, row.elder_id)
    return FamilyMemberVO(
        id=row.id or 0,
        user_id=row.user_id,
        elder_id=row.elder_id,
        relation=row.relation,
        is_primary=row.is_primary,
        username=user.username if user else None,
        nickname=user.nickname if user else None,
        elder_name=elder.name if elder else None,
        create_time=row.create_time,
    )


def page_schedules(
    db: Session,
    current: int,
    size: int,
    elder_id: int | None,
) -> PageResult[MedicationScheduleVO]:
    current = max(1, current)
    size = min(100, max(1, size))
    stmt = select(MedicationSchedule)
    count_stmt = select(func.count()).select_from(MedicationSchedule)
    if elder_id is not None:
        stmt = stmt.where(MedicationSchedule.elder_id == elder_id)
        count_stmt = count_stmt.where(MedicationSchedule.elder_id == elder_id)
    total = db.exec(count_stmt).one()
    rows = db.exec(
        stmt.order_by(col(MedicationSchedule.id).desc())
        .offset((current - 1) * size)
        .limit(size)
    ).all()
    return PageResult(
        records=[_schedule_to_vo(db, r) for r in rows],
        total=total,
        current=current,
        size=size,
    )


def list_schedules_for_elder(
    db: Session, elder_id: int, user: User
) -> list[MedicationScheduleVO]:
    assert_family_access(db, user, elder_id)
    rows = db.exec(
        select(MedicationSchedule)
        .where(MedicationSchedule.elder_id == elder_id)
        .order_by(col(MedicationSchedule.id).desc())
    ).all()
    return [_schedule_to_vo(db, r) for r in rows]


def create_schedule(
    db: Session, body: MedicationScheduleSaveRequest
) -> MedicationScheduleVO:
    if db.get(ElderProfile, body.elder_id) is None:
        raise BusinessException("老人档案不存在")
    now = datetime.now()
    row = MedicationSchedule(
        **body.model_dump(),
        create_time=now,
        update_time=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _schedule_to_vo(db, row)


def update_schedule(
    db: Session, schedule_id: int, body: MedicationScheduleSaveRequest
) -> MedicationScheduleVO:
    row = db.get(MedicationSchedule, schedule_id)
    if row is None:
        raise BusinessException("用药计划不存在")
    for k, v in body.model_dump().items():
        setattr(row, k, v)
    row.update_time = datetime.now()
    db.add(row)
    db.commit()
    db.refresh(row)
    return _schedule_to_vo(db, row)


def delete_schedule(db: Session, schedule_id: int) -> None:
    row = db.get(MedicationSchedule, schedule_id)
    if row is None:
        raise BusinessException("用药计划不存在")
    db.delete(row)
    db.commit()


def _schedule_to_vo(db: Session, row: MedicationSchedule) -> MedicationScheduleVO:
    elder = db.get(ElderProfile, row.elder_id)
    vo = MedicationScheduleVO.model_validate(row)
    vo.elder_name = elder.name if elder else None
    return vo


def page_medication_logs(
    db: Session,
    current: int,
    size: int,
    elder_id: int | None,
    status: int | None,
    user: User | None = None,
) -> PageResult[MedicationLogVO]:
    current = max(1, current)
    size = min(100, max(1, size))
    stmt = select(MedicationLog)
    count_stmt = select(func.count()).select_from(MedicationLog)
    if user is not None and user.role != "ADMIN":
        bound = list_bound_elder_ids(db, user.id or 0)
        if not bound:
            return PageResult(records=[], total=0, current=current, size=size)
        if elder_id is not None:
            assert_family_access(db, user, elder_id)
            stmt = stmt.where(MedicationLog.elder_id == elder_id)
            count_stmt = count_stmt.where(MedicationLog.elder_id == elder_id)
        else:
            stmt = stmt.where(col(MedicationLog.elder_id).in_(bound))
            count_stmt = count_stmt.where(col(MedicationLog.elder_id).in_(bound))
    elif elder_id is not None:
        stmt = stmt.where(MedicationLog.elder_id == elder_id)
        count_stmt = count_stmt.where(MedicationLog.elder_id == elder_id)
    if status is not None:
        stmt = stmt.where(MedicationLog.status == status)
        count_stmt = count_stmt.where(MedicationLog.status == status)
    total = db.exec(count_stmt).one()
    rows = db.exec(
        stmt.order_by(col(MedicationLog.planned_time).desc())
        .offset((current - 1) * size)
        .limit(size)
    ).all()
    return PageResult(
        records=[_medication_log_to_vo(db, r) for r in rows],
        total=total,
        current=current,
        size=size,
    )


def mark_taken(db: Session, log_id: int, user: User) -> MedicationLogVO:
    """子女/管理员标记某条用药记录为已服。"""
    row = db.get(MedicationLog, log_id)
    if row is None:
        raise BusinessException("用药记录不存在")
    assert_family_access(db, user, row.elder_id)
    if row.status == 1:
        return _medication_log_to_vo(db, row)
    row.status = 1
    row.taken_time = datetime.now()
    db.add(row)
    db.commit()
    db.refresh(row)
    return _medication_log_to_vo(db, row)


def _medication_log_to_vo(db: Session, row: MedicationLog) -> MedicationLogVO:
    sched = db.get(MedicationSchedule, row.schedule_id)
    elder = db.get(ElderProfile, row.elder_id)
    return MedicationLogVO(
        id=row.id or 0,
        schedule_id=row.schedule_id,
        elder_id=row.elder_id,
        planned_time=row.planned_time,
        taken_time=row.taken_time,
        status=row.status,
        drug_name=sched.drug_name if sched else None,
        elder_name=elder.name if elder else None,
        create_time=row.create_time,
    )


def list_catalog(db: Session, only_active: bool = True) -> list[ServiceCatalogVO]:
    stmt = select(ServiceCatalog)
    if only_active:
        stmt = stmt.where(ServiceCatalog.status == 1)
    rows = db.exec(stmt.order_by(col(ServiceCatalog.id).asc())).all()
    return [ServiceCatalogVO.model_validate(r) for r in rows]


def page_catalog(
    db: Session, current: int, size: int
) -> PageResult[ServiceCatalogVO]:
    current = max(1, current)
    size = min(100, max(1, size))
    total = db.exec(select(func.count()).select_from(ServiceCatalog)).one()
    rows = db.exec(
        select(ServiceCatalog)
        .order_by(col(ServiceCatalog.id).asc())
        .offset((current - 1) * size)
        .limit(size)
    ).all()
    return PageResult(
        records=[ServiceCatalogVO.model_validate(r) for r in rows],
        total=total,
        current=current,
        size=size,
    )


def save_catalog(
    db: Session, body: ServiceCatalogSaveRequest, catalog_id: int | None = None
) -> ServiceCatalogVO:
    now = datetime.now()
    if catalog_id is None:
        row = ServiceCatalog(**body.model_dump(), create_time=now, update_time=now)
        db.add(row)
    else:
        row = db.get(ServiceCatalog, catalog_id)
        if row is None:
            raise BusinessException("服务目录不存在")
        for k, v in body.model_dump().items():
            setattr(row, k, v)
        row.update_time = now
        db.add(row)
    db.commit()
    db.refresh(row)
    return ServiceCatalogVO.model_validate(row)


def query_slots(
    db: Session,
    service_type: str | None,
    catalog_id: int | None,
    days: int = 7,
) -> list[ServiceSlotsVO]:
    """查询近若干天可预约时段（排除 pending/confirmed 占用）。"""
    stmt = select(ServiceCatalog).where(ServiceCatalog.status == 1)
    if catalog_id is not None:
        stmt = stmt.where(ServiceCatalog.id == catalog_id)
    elif service_type:
        stmt = stmt.where(ServiceCatalog.service_type == service_type)
    catalogs = db.exec(stmt).all()
    if not catalogs:
        return []
    result: list[ServiceSlotsVO] = []
    base = datetime.now().replace(minute=0, second=0, microsecond=0)
    for cat in catalogs:
        slots: list[str] = []
        for d in range(1, max(1, days) + 1):
            for hour in (9, 14):
                slot = (base + timedelta(days=d)).replace(hour=hour)
                conflict = db.exec(
                    select(func.count())
                    .select_from(ServiceBooking)
                    .where(
                        ServiceBooking.catalog_id == cat.id,
                        ServiceBooking.booking_time == slot,
                        col(ServiceBooking.status).in_(["pending", "confirmed"]),
                    )
                ).one()
                if not conflict:
                    slots.append(slot.strftime("%Y-%m-%d %H:%M"))
        result.append(
            ServiceSlotsVO(
                catalog_id=cat.id or 0,
                service_type=cat.service_type,
                catalog_name=cat.name,
                slots=slots,
            )
        )
    return result


def _booking_slot_lock(catalog_id: int, booking_time: datetime) -> str:
    """有效预约的时段锁键（同一服务同一分钟唯一）。"""
    return f"{catalog_id}:{booking_time.strftime('%Y%m%d%H%M')}"


def create_booking(
    db: Session,
    body: ServiceBookingCreateRequest,
    user: User,
    source: str = "manual",
) -> ServiceBookingVO:
    """创建预约；source=agent 表示由智能助手写入。"""
    assert_family_access(db, user, body.elder_id)
    catalog = db.get(ServiceCatalog, body.catalog_id)
    if catalog is None or catalog.status != 1:
        raise BusinessException("服务不存在或已下架")
    conflict = db.exec(
        select(ServiceBooking).where(
            ServiceBooking.catalog_id == body.catalog_id,
            ServiceBooking.booking_time == body.booking_time,
            col(ServiceBooking.status).in_(["pending", "confirmed"]),
        )
    ).first()
    if conflict:
        raise BusinessException("该时段已被预约")
    now = datetime.now()
    row = ServiceBooking(
        elder_id=body.elder_id,
        catalog_id=body.catalog_id,
        booking_time=body.booking_time,
        status="pending",
        source=source,
        remark=body.remark,
        slot_lock=_booking_slot_lock(body.catalog_id, body.booking_time),
        version=0,
        create_time=now,
        update_time=now,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # UNIQUE(uk_booking_slot_lock) 冲突：并发下另一请求已占同时段
        raise BusinessException("该时段刚被他人预约，请刷新后重选") from exc
    db.refresh(row)
    return _booking_to_vo(db, row)


def page_bookings(
    db: Session,
    current: int,
    size: int,
    elder_id: int | None,
    status: str | None,
    user: User | None = None,
) -> PageResult[ServiceBookingVO]:
    if user is not None and user.role != "ADMIN":
        if elder_id is None:
            ids = list_bound_elder_ids(db, user.id or 0)
            if not ids:
                return PageResult(records=[], total=0, current=current, size=size)
        else:
            assert_family_access(db, user, elder_id)
            ids = [elder_id]
    else:
        ids = [elder_id] if elder_id is not None else None

    current = max(1, current)
    size = min(100, max(1, size))
    stmt = select(ServiceBooking)
    count_stmt = select(func.count()).select_from(ServiceBooking)
    if ids is not None:
        stmt = stmt.where(col(ServiceBooking.elder_id).in_(ids))
        count_stmt = count_stmt.where(col(ServiceBooking.elder_id).in_(ids))
    if status:
        stmt = stmt.where(ServiceBooking.status == status)
        count_stmt = count_stmt.where(ServiceBooking.status == status)
    total = db.exec(count_stmt).one()
    rows = db.exec(
        stmt.order_by(col(ServiceBooking.booking_time).desc())
        .offset((current - 1) * size)
        .limit(size)
    ).all()
    return PageResult(
        records=[_booking_to_vo(db, r) for r in rows],
        total=total,
        current=current,
        size=size,
    )


def update_booking(
    db: Session, booking_id: int, body: ServiceBookingUpdateRequest
) -> ServiceBookingVO:
    row = db.get(ServiceBooking, booking_id)
    if row is None:
        raise BusinessException("预约不存在")
    expected_version = int(row.version or 0)
    data = body.model_dump(exclude_unset=True)
    if "status" in data and data["status"] is not None:
        if data["status"] not in ("pending", "confirmed", "cancelled", "done"):
            raise BusinessException("预约状态无效")

    new_status = data.get("status", row.status) or row.status
    new_remark = data["remark"] if "remark" in data else row.remark
    new_time = data.get("booking_time", row.booking_time) or row.booking_time
    if new_status in ("pending", "confirmed"):
        new_lock = _booking_slot_lock(row.catalog_id, new_time)
    else:
        new_lock = None

    from sqlalchemy import text

    now = datetime.now()
    result = db.execute(
        text(
            """
            UPDATE service_booking
            SET booking_time = :booking_time,
                status = :status,
                remark = :remark,
                slot_lock = :slot_lock,
                version = version + 1,
                update_time = :update_time
            WHERE id = :id AND version = :version
            """
        ),
        {
            "booking_time": new_time,
            "status": new_status,
            "remark": new_remark,
            "slot_lock": new_lock,
            "update_time": now,
            "id": booking_id,
            "version": expected_version,
        },
    )
    if result.rowcount == 0:
        db.rollback()
        raise BusinessException("预约已被他人修改，请刷新后重试")
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise BusinessException("时段冲突，请刷新后重试") from exc

    updated = db.get(ServiceBooking, booking_id)
    if updated is None:
        raise BusinessException("预约不存在")
    return _booking_to_vo(db, updated)


def _booking_to_vo(db: Session, row: ServiceBooking) -> ServiceBookingVO:
    elder = db.get(ElderProfile, row.elder_id)
    catalog = db.get(ServiceCatalog, row.catalog_id)
    return ServiceBookingVO(
        id=row.id or 0,
        elder_id=row.elder_id,
        catalog_id=row.catalog_id,
        booking_time=row.booking_time,
        status=row.status,
        source=row.source,
        remark=row.remark,
        elder_name=elder.name if elder else None,
        catalog_name=catalog.name if catalog else None,
        service_type=catalog.service_type if catalog else None,
        create_time=row.create_time,
        update_time=row.update_time,
    )


def care_dashboard(db: Session, user: User) -> CareDashboardVO:
    """子女关怀看板：绑定老人、近期漏服与预约摘要。"""
    elders = my_elders(db, user)
    ids = [e.id for e in elders]
    missed: list[MedicationLogVO] = []
    bookings: list[ServiceBookingVO] = []
    if ids:
        since = datetime.now() - timedelta(days=7)
        log_rows = db.exec(
            select(MedicationLog)
            .where(
                col(MedicationLog.elder_id).in_(ids),
                MedicationLog.status == 0,
                MedicationLog.planned_time >= since,
            )
            .order_by(col(MedicationLog.planned_time).desc())
            .limit(10)
        ).all()
        missed = [_medication_log_to_vo(db, r) for r in log_rows]
        book_rows = db.exec(
            select(ServiceBooking)
            .where(col(ServiceBooking.elder_id).in_(ids))
            .order_by(col(ServiceBooking.booking_time).desc())
            .limit(10)
        ).all()
        bookings = [_booking_to_vo(db, r) for r in book_rows]
    return CareDashboardVO(
        elders=elders, recent_missed=missed, recent_bookings=bookings
    )
