from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from app.common.result import CamelModel


class AgentChatRequest(CamelModel):
    session_id: Optional[str] = None
    elder_id: int
    message: str = Field(min_length=1, max_length=2000)


class AgentStepVO(CamelModel):
    round: int
    thought: Optional[str] = None
    action: Optional[str] = None
    observation: Optional[str] = None


class AgentPendingConfirmVO(CamelModel):
    type: Optional[str] = None
    catalog_id: Optional[int] = None
    catalog_name: Optional[str] = None
    options: list[str] = []


class AgentChatResponse(CamelModel):
    session_id: str
    reply: str
    steps: list[AgentStepVO] = []
    pending_confirm: Optional[dict[str, Any]] = None
    demo_mode: bool = True


class AgentMessageVO(CamelModel):
    id: Optional[int] = None
    role: str
    content: str
    create_time: Optional[datetime] = None


class AgentSessionVO(CamelModel):
    session_id: str
    elder_id: Optional[int] = None
    preview: Optional[str] = None
    create_time: Optional[datetime] = None
