from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.common.result import PageResult, Result
from app.core.deps import get_current_user, get_db, require_admin
from app.models import User
from app.schemas.admin_stats import AdminStatsVO
from app.schemas.elder import AgentToolCallLogVO, CareDashboardVO
from app.services import admin_stats_service, agent_log_service, elder_service

router = APIRouter(tags=["关怀看板与Agent日志"])


@router.get("/care/dashboard")
def care_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[CareDashboardVO]:
    return Result.ok(elder_service.care_dashboard(db, current_user))


@router.get("/admin/stats")
def admin_stats(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Result[AdminStatsVO]:
    return Result.ok(admin_stats_service.get_admin_stats(db))


@router.get("/admin/agent/tool-logs")
def page_tool_logs(
    current: int = 1,
    size: int = 10,
    tool_name: str | None = None,
    session_id: str | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Result[PageResult[AgentToolCallLogVO]]:
    return Result.ok(
        agent_log_service.page_tool_logs(
            db, current, size, tool_name, session_id
        )
    )


@router.get("/admin/agent/tools")
def list_agent_tools(
    _admin: User = Depends(require_admin),
) -> Result[list]:
    """Agent 工具目录：用途与使用规则（管理端说明页）。"""
    from app.agent.tool_catalog import list_tool_catalog

    return Result.ok(list_tool_catalog())
