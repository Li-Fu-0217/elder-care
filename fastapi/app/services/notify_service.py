from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, col, select

from app.common.exceptions import BusinessException
from app.common.result import PageResult
from app.models import ElderProfile, FamilyMember, NotifyInbox, User
from app.schemas.notify import NotifyInboxVO, UnreadCountVO


MSG_TYPE_LABELS = {
    "agent_notify": "智能提醒",
    "medication": "用药提醒",
    "booking": "预约通知",
    "emergency": "紧急告警",
    "system": "系统通知",
}


def notify_family_members(
    db: Session,
    *,
    elder_id: int,
    title: str,
    content: str,
    msg_type: str = "agent_notify",
    source: str = "agent",
    related_id: int | None = None,
    exclude_user_id: int | None = None,
) -> list[NotifyInbox]:
    """向绑定该老人的家属写入站内消息。"""
    stmt = select(FamilyMember).where(FamilyMember.elder_id == elder_id)
    rows = db.exec(stmt).all()
    now = datetime.now()
    created: list[NotifyInbox] = []
    seen: set[int] = set()
    for fm in rows:
        uid = fm.user_id
        if uid is None or uid in seen:
            continue
        if exclude_user_id is not None and uid == exclude_user_id:
            continue
        seen.add(uid)
        item = NotifyInbox(
            user_id=uid,
            elder_id=elder_id,
            title=title[:100],
            content=content,
            msg_type=msg_type,
            source=source,
            related_id=related_id,
            is_read=0,
            create_time=now,
            update_time=now,
        )
        db.add(item)
        created.append(item)
    if created:
        db.commit()
        for item in created:
            db.refresh(item)
    return created


def page_my_notifications(
    db: Session,
    user: User,
    current: int,
    size: int,
    is_read: int | None = None,
) -> PageResult[NotifyInboxVO]:
    current = max(1, current)
    size = min(100, max(1, size))
    uid = user.id or 0
    stmt = select(NotifyInbox).where(NotifyInbox.user_id == uid)
    count_stmt = (
        select(func.count()).select_from(NotifyInbox).where(NotifyInbox.user_id == uid)
    )
    if is_read is not None:
        stmt = stmt.where(NotifyInbox.is_read == is_read)
        count_stmt = count_stmt.where(NotifyInbox.is_read == is_read)
    total = db.exec(count_stmt).one()
    rows = db.exec(
        stmt.order_by(col(NotifyInbox.id).desc())
        .offset((current - 1) * size)
        .limit(size)
    ).all()
    return PageResult(
        records=[_to_vo(db, r) for r in rows],
        total=total,
        current=current,
        size=size,
    )


def unread_count(db: Session, user: User) -> UnreadCountVO:
    uid = user.id or 0
    total = db.exec(
        select(func.count())
        .select_from(NotifyInbox)
        .where(NotifyInbox.user_id == uid, NotifyInbox.is_read == 0)
    ).one()
    return UnreadCountVO(count=int(total or 0))


def mark_read(db: Session, user: User, notify_id: int) -> NotifyInboxVO:
    row = db.get(NotifyInbox, notify_id)
    if row is None or row.user_id != user.id:
        raise BusinessException("消息不存在")
    if row.is_read != 1:
        row.is_read = 1
        row.update_time = datetime.now()
        db.add(row)
        db.commit()
        db.refresh(row)
    return _to_vo(db, row)


def mark_all_read(db: Session, user: User) -> UnreadCountVO:
    uid = user.id or 0
    rows = db.exec(
        select(NotifyInbox).where(NotifyInbox.user_id == uid, NotifyInbox.is_read == 0)
    ).all()
    now = datetime.now()
    for row in rows:
        row.is_read = 1
        row.update_time = now
        db.add(row)
    if rows:
        db.commit()
    return unread_count(db, user)


def _to_vo(db: Session, row: NotifyInbox) -> NotifyInboxVO:
    elder_name = None
    if row.elder_id:
        elder = db.get(ElderProfile, row.elder_id)
        elder_name = elder.name if elder else None
    return NotifyInboxVO(
        id=row.id or 0,
        user_id=row.user_id,
        elder_id=row.elder_id,
        elder_name=elder_name,
        title=row.title,
        content=row.content,
        msg_type=row.msg_type,
        source=row.source,
        related_id=row.related_id,
        is_read=row.is_read,
        create_time=row.create_time,
    )
