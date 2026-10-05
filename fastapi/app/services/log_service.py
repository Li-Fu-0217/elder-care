from sqlmodel import Session, col, func, select

from app.common.exceptions import BusinessException
from app.common.result import PageResult
from app.models import LoginLog, OperationLog
from app.schemas import SystemLogVO


def page_logs(
    db: Session,
    current: int,
    size: int,
    username: str | None,
    log_type: str,
) -> PageResult[SystemLogVO]:
    current = max(1, current)
    size = min(100, max(1, size))
    log_type = (log_type or "login").lower()
    if log_type == "login":
        stmt = select(LoginLog)
        count_stmt = select(func.count()).select_from(LoginLog)
        if username and username.strip():
            kw = f"%{username.strip()}%"
            stmt = stmt.where(col(LoginLog.username).like(kw))
            count_stmt = count_stmt.where(col(LoginLog.username).like(kw))
        total = db.exec(count_stmt).one()
        rows = db.exec(
            stmt.order_by(col(LoginLog.create_time).desc())
            .offset((current - 1) * size)
            .limit(size)
        ).all()
        records = [
            SystemLogVO(
                id=r.id,  # type: ignore[arg-type]
                log_type="LOGIN",
                log_type_name="登录",
                username=r.username,
                ip=r.ip,
                status=r.status,
                message=r.message,
                create_time=r.create_time,
            )
            for r in rows
        ]
    elif log_type == "operation":
        stmt = select(OperationLog)
        count_stmt = select(func.count()).select_from(OperationLog)
        if username and username.strip():
            kw = f"%{username.strip()}%"
            stmt = stmt.where(col(OperationLog.username).like(kw))
            count_stmt = count_stmt.where(col(OperationLog.username).like(kw))
        total = db.exec(count_stmt).one()
        rows = db.exec(
            stmt.order_by(col(OperationLog.create_time).desc())
            .offset((current - 1) * size)
            .limit(size)
        ).all()
        records = [
            SystemLogVO(
                id=r.id,  # type: ignore[arg-type]
                log_type="OPERATION",
                log_type_name="操作",
                username=r.username,
                module=r.module,
                action=r.action,
                method=r.method,
                url=r.url,
                ip=r.ip,
                cost_ms=r.cost_ms,
                status=r.status,
                create_time=r.create_time,
            )
            for r in rows
        ]
    else:
        raise BusinessException("日志类型无效")
    return PageResult(records=records, total=total, current=current, size=size)


def batch_delete(db: Session, log_type: str, ids: list[int]) -> None:
    if not ids:
        raise BusinessException("请选择要删除的日志")
    log_type = (log_type or "").lower()
    if log_type == "login":
        for lid in ids:
            row = db.get(LoginLog, lid)
            if row:
                db.delete(row)
    elif log_type == "operation":
        for lid in ids:
            row = db.get(OperationLog, lid)
            if row:
                db.delete(row)
    else:
        raise BusinessException("日志类型无效")
    db.commit()
