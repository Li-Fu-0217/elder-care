"""管理端数据概览统计。"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlmodel import Session, col, func, select

from app.models import (
    AgentToolCallLog,
    CommunityActivity,
    ElderProfile,
    EmergencyAlert,
    KnowledgeDocument,
    MedicationLog,
    ServiceBooking,
    ServiceCatalog,
    User,
)
from app.schemas.admin_stats import (
    AdminStatsVO,
    ChartSeriesVO,
    NamedValueVO,
    StatCardVO,
)

_BOOKING_STATUS_LABEL = {
    "pending": "待确认",
    "confirmed": "已确认",
    "cancelled": "已取消",
    "done": "已完成",
}

_SERVICE_TYPE_LABEL = {
    "health_check": "体检",
    "nursing": "护理",
    "housekeeping": "家政",
}

_TOOL_LABEL = {
    "query_health_record": "健康档案",
    "check_medication_schedule": "用药漏服",
    "query_available_service": "查时段",
    "book_service": "预约",
    "notify_family": "通知子女",
    "trigger_emergency_alert": "紧急告警",
    "query_knowledge_base": "知识库",
}


def get_admin_stats(db: Session) -> AdminStatsVO:
    elder_count = _count(db, select(func.count()).select_from(ElderProfile))
    user_count = _count(
        db, select(func.count()).select_from(User).where(User.role == "USER")
    )
    pending_bookings = _count(
        db,
        select(func.count())
        .select_from(ServiceBooking)
        .where(ServiceBooking.status == "pending"),
    )
    open_alerts = _count(
        db,
        select(func.count())
        .select_from(EmergencyAlert)
        .where(col(EmergencyAlert.status).in_(["open", "handling"])),
    )
    activity_count = _count(
        db,
        select(func.count())
        .select_from(CommunityActivity)
        .where(CommunityActivity.status == 1),
    )
    knowledge_ready = _count(
        db,
        select(func.count())
        .select_from(KnowledgeDocument)
        .where(KnowledgeDocument.status == 1),
    )
    since = datetime.now() - timedelta(days=3)
    missed_meds = _count(
        db,
        select(func.count())
        .select_from(MedicationLog)
        .where(
            MedicationLog.status == 0,
            MedicationLog.planned_time >= since,
        ),
    )
    tool_calls = _count(db, select(func.count()).select_from(AgentToolCallLog))

    cards = [
        StatCardVO(key="elders", label="在册老人", value=elder_count, hint="档案总数"),
        StatCardVO(key="users", label="子女用户", value=user_count, hint="USER 角色"),
        StatCardVO(
            key="pendingBookings",
            label="待确认预约",
            value=pending_bookings,
            hint="需后台处理",
        ),
        StatCardVO(
            key="openAlerts",
            label="未关闭告警",
            value=open_alerts,
            hint="open / handling",
        ),
        StatCardVO(
            key="activities",
            label="上架活动",
            value=activity_count,
            hint="可报名",
        ),
        StatCardVO(
            key="missedMeds",
            label="近3日漏服",
            value=missed_meds,
            hint="用药记录",
        ),
        StatCardVO(
            key="knowledge",
            label="知识库文档",
            value=knowledge_ready,
            hint="已就绪",
        ),
        StatCardVO(
            key="toolCalls",
            label="工具调用次数",
            value=tool_calls,
            hint="Agent 累计",
        ),
    ]

    return AdminStatsVO(
        cards=cards,
        booking_status=_booking_status(db),
        booking_by_service=_booking_by_service(db),
        booking_trend_dates=_trend_dates(),
        booking_trend_series=_booking_trend(db),
        tool_usage=_tool_usage(db),
    )


def _count(db: Session, stmt) -> int:
    return int(db.exec(stmt).one() or 0)


def _booking_status(db: Session) -> list[NamedValueVO]:
    rows = db.exec(
        select(ServiceBooking.status, func.count())
        .group_by(ServiceBooking.status)
    ).all()
    by_status = {str(s): int(c) for s, c in rows}
    out: list[NamedValueVO] = []
    for key in ("pending", "confirmed", "done", "cancelled"):
        out.append(
            NamedValueVO(
                name=_BOOKING_STATUS_LABEL.get(key, key),
                value=by_status.get(key, 0),
            )
        )
    return out


def _booking_by_service(db: Session) -> list[NamedValueVO]:
    rows = db.exec(
        select(ServiceCatalog.service_type, func.count())
        .select_from(ServiceBooking)
        .join(ServiceCatalog, ServiceBooking.catalog_id == ServiceCatalog.id)
        .group_by(ServiceCatalog.service_type)
    ).all()
    by_type = {str(t): int(c) for t, c in rows}
    out: list[NamedValueVO] = []
    for key in ("health_check", "nursing", "housekeeping"):
        out.append(
            NamedValueVO(
                name=_SERVICE_TYPE_LABEL.get(key, key),
                value=by_type.get(key, 0),
            )
        )
    # 其它类型（若有）
    for key, val in by_type.items():
        if key not in _SERVICE_TYPE_LABEL:
            out.append(NamedValueVO(name=key, value=val))
    return out


def _trend_dates() -> list[str]:
    today = datetime.now().date()
    return [(today - timedelta(days=i)).strftime("%m-%d") for i in range(6, -1, -1)]


def _booking_trend(db: Session) -> list[ChartSeriesVO]:
    today = datetime.now().date()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    start = datetime.combine(days[0], datetime.min.time())

    rows = db.exec(
        select(ServiceBooking.booking_time, ServiceBooking.status).where(
            ServiceBooking.booking_time >= start
        )
    ).all()

    created = {d: 0 for d in days}
    confirmed = {d: 0 for d in days}
    for bt, status in rows:
        d = bt.date() if hasattr(bt, "date") else bt
        if d not in created:
            continue
        created[d] += 1
        if status in ("confirmed", "done"):
            confirmed[d] += 1

    return [
        ChartSeriesVO(name="预约数", data=[created[d] for d in days]),
        ChartSeriesVO(name="已确认/完成", data=[confirmed[d] for d in days]),
    ]


def _tool_usage(db: Session) -> list[NamedValueVO]:
    rows = db.exec(
        select(AgentToolCallLog.tool_name, func.count())
        .group_by(AgentToolCallLog.tool_name)
        .order_by(func.count().desc())
    ).all()
    out: list[NamedValueVO] = []
    for name, cnt in rows:
        key = str(name)
        out.append(
            NamedValueVO(
                name=_TOOL_LABEL.get(key, key),
                value=int(cnt),
            )
        )
    if not out:
        # 占位，避免空图
        out = [NamedValueVO(name="暂无调用", value=0)]
    return out[:8]
