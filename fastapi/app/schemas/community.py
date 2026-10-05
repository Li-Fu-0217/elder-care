from datetime import datetime
from typing import Optional

from pydantic import Field

from app.common.result import CamelModel


class ActivityVO(CamelModel):
    id: int
    title: str
    content: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    capacity: Optional[int] = None
    status: int
    registered_count: int = 0
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class ActivitySaveRequest(CamelModel):
    title: str = Field(min_length=1, max_length=100)
    content: Optional[str] = None
    location: Optional[str] = Field(default=None, max_length=200)
    start_time: datetime
    end_time: Optional[datetime] = None
    capacity: Optional[int] = None
    status: int = 1


class ActivityRegisterRequest(CamelModel):
    elder_id: int


class ActivityRegistrationVO(CamelModel):
    id: int
    activity_id: int
    elder_id: int
    user_id: Optional[int] = None
    status: str
    activity_title: Optional[str] = None
    elder_name: Optional[str] = None
    create_time: Optional[datetime] = None


class EmergencyAlertVO(CamelModel):
    id: int
    elder_id: int
    location: Optional[str] = None
    message: Optional[str] = None
    status: str
    notify_family: int
    notify_staff: int
    source: str
    elder_name: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class EmergencyAlertCreateRequest(CamelModel):
    elder_id: int
    location: Optional[str] = Field(default=None, max_length=200)
    message: Optional[str] = None


class EmergencyAlertUpdateRequest(CamelModel):
    status: str
    notify_family: Optional[int] = None
    notify_staff: Optional[int] = None
