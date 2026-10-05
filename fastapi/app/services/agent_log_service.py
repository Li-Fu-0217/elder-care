from sqlmodel import Session, col, func, select

from app.common.result import PageResult
from app.models import AgentToolCallLog
from app.schemas.elder import AgentToolCallLogVO


def page_tool_logs(
    db: Session,
    current: int,
    size: int,
    tool_name: str | None = None,
    session_id: str | None = None,
) -> PageResult[AgentToolCallLogVO]:
    current = max(1, current)
    size = min(100, max(1, size))
    stmt = select(AgentToolCallLog)
    count_stmt = select(func.count()).select_from(AgentToolCallLog)
    if tool_name and tool_name.strip():
        cond = AgentToolCallLog.tool_name == tool_name.strip()
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    if session_id and session_id.strip():
        cond = AgentToolCallLog.session_id == session_id.strip()
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    total = db.exec(count_stmt).one()
    rows = db.exec(
        stmt.order_by(col(AgentToolCallLog.id).desc())
        .offset((current - 1) * size)
        .limit(size)
    ).all()
    return PageResult(
        records=[AgentToolCallLogVO.model_validate(r) for r in rows],
        total=total,
        current=current,
        size=size,
    )
