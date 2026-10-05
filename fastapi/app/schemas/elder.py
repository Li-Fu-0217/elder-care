from datetime import date, datetime
from typing import Optional

from pydantic import Field, field_validator

from app.common.result import CamelModel


class ElderVO(CamelModel):
    id: int
    name: str
    gender: Optional[int] = None
    birth_date: Optional[date] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    chronic_diseases: Optional[str] = None
    current_medications: Optional[str] = None
    health_summary: Optional[str] = None
    status: int
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class ElderSaveRequest(CamelModel):
    name: str = Field(min_length=1, max_length=50)
    gender: Optional[int] = None
    birth_date: Optional[date] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=200)
    emergency_contact: Optional[str] = Field(default=None, max_length=50)
    emergency_phone: Optional[str] = Field(default=None, max_length=20)
    chronic_diseases: Optional[str] = None
    current_medications: Optional[str] = None
    health_summary: Optional[str] = None
    status: int = 1

    @field_validator("name")
    @classmethod
    def name_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("姓名不能为空")
        return v.strip()


class ElderHealthVO(CamelModel):
    elder_id: int
    name: str
    chronic_diseases: Optional[str] = None
    current_medications: Optional[str] = None
    health_summary: Optional[str] = None
    recent_missed_count: int = 0
    recent_missed_logs: list["MedicationLogVO"] = []


class FamilyMemberVO(CamelModel):
    id: int
    user_id: int
    elder_id: int
    relation: Optional[str] = None
    is_primary: int
    username: Optional[str] = None
    nickname: Optional[str] = None
    elder_name: Optional[str] = None
    create_time: Optional[datetime] = None


class FamilyBindRequest(CamelModel):
    """管理端绑定可用 username；自助绑定传 user_id。二者填其一。"""

    user_id: Optional[int] = None
    username: Optional[str] = Field(default=None, max_length=50)
    elder_id: int
    relation: Optional[str] = Field(default=None, max_length=20)
    is_primary: int = 0


class UserSelfBindRequest(CamelModel):
    """子女自助绑定：姓名+手机号须与老人档案一致。"""

    elder_name: str = Field(min_length=1, max_length=50)
    elder_phone: str = Field(min_length=5, max_length=20)
    relation: Optional[str] = Field(default="家属", max_length=20)
    is_primary: int = 0


class MedicationScheduleVO(CamelModel):
    id: int
    elder_id: int
    drug_name: str
    dosage: Optional[str] = None
    schedule_times: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    remark: Optional[str] = None
    status: int
    elder_name: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class MedicationScheduleSaveRequest(CamelModel):
    elder_id: int
    drug_name: str = Field(min_length=1, max_length=100)
    dosage: Optional[str] = Field(default=None, max_length=50)
    schedule_times: str = Field(min_length=1, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    remark: Optional[str] = Field(default=None, max_length=200)
    status: int = 1


class MedicationLogVO(CamelModel):
    id: int
    schedule_id: int
    elder_id: int
    planned_time: datetime
    taken_time: Optional[datetime] = None
    status: int
    drug_name: Optional[str] = None
    elder_name: Optional[str] = None
    create_time: Optional[datetime] = None


class ServiceCatalogVO(CamelModel):
    id: int
    name: str
    service_type: str
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    status: int
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class ServiceCatalogSaveRequest(CamelModel):
    name: str = Field(min_length=1, max_length=100)
    service_type: str = Field(min_length=1, max_length=50)
    description: Optional[str] = None
    duration_minutes: Optional[int] = 60
    status: int = 1


class ServiceBookingVO(CamelModel):
    id: int
    elder_id: int
    catalog_id: int
    booking_time: datetime
    status: str
    source: str
    remark: Optional[str] = None
    elder_name: Optional[str] = None
    catalog_name: Optional[str] = None
    service_type: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class ServiceBookingCreateRequest(CamelModel):
    elder_id: int
    catalog_id: int
    booking_time: datetime
    remark: Optional[str] = Field(default=None, max_length=200)


class ServiceBookingUpdateRequest(CamelModel):
    booking_time: Optional[datetime] = None
    status: Optional[str] = None
    remark: Optional[str] = Field(default=None, max_length=200)


class ServiceSlotsVO(CamelModel):
    catalog_id: int
    service_type: str
    catalog_name: str
    slots: list[str]


class CareDashboardVO(CamelModel):
    elders: list[ElderVO]
    recent_missed: list[MedicationLogVO]
    recent_bookings: list[ServiceBookingVO]


class AgentToolCallLogVO(CamelModel):
    id: int
    session_id: str
    conversation_id: Optional[int] = None
    user_id: int
    tool_name: str
    request_args: Optional[str] = None
    response_data: Optional[str] = None
    status: int
    cost_ms: Optional[int] = None
    create_time: Optional[datetime] = None


ElderHealthVO.model_rebuild()
