from datetime import datetime
from typing import Optional

from app.common.result import CamelModel


class NotifyInboxVO(CamelModel):
    id: int
    user_id: int
    elder_id: Optional[int] = None
    elder_name: Optional[str] = None
    title: str
    content: str
    msg_type: str
    source: str
    related_id: Optional[int] = None
    is_read: int
    create_time: Optional[datetime] = None


class UnreadCountVO(CamelModel):
    count: int
