from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.agent import react as agent_react
from app.common.result import Result
from app.core.deps import get_current_user, get_db
from app.models import User
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    AgentMessageVO,
    AgentSessionVO,
    AgentStepVO,
)
from app.services import elder_service

router = APIRouter(prefix="/agent", tags=["Agent对话"])


@router.post("/chat")
def agent_chat(
    body: AgentChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[AgentChatResponse]:
    elder_service.assert_family_access(db, current_user, body.elder_id)
    raw = agent_react.chat(
        db,
        current_user,
        elder_id=body.elder_id,
        message=body.message.strip(),
        session_id=body.session_id,
    )
    steps = [AgentStepVO.model_validate(s) for s in raw.get("steps") or []]
    return Result.ok(
        AgentChatResponse(
            session_id=raw["sessionId"],
            reply=raw["reply"],
            steps=steps,
            pending_confirm=raw.get("pendingConfirm"),
            demo_mode=bool(raw.get("demoMode", True)),
        )
    )


@router.get("/sessions")
def agent_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[list[AgentSessionVO]]:
    rows = agent_react.list_sessions(db, current_user)
    return Result.ok([AgentSessionVO.model_validate(r) for r in rows])


@router.get("/sessions/{session_id}/messages")
def agent_messages(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[list[AgentMessageVO]]:
    rows = agent_react.list_messages(db, current_user, session_id)
    return Result.ok([AgentMessageVO.model_validate(r) for r in rows])
