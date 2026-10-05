from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ElderProfile(SQLModel, table=True):
    __tablename__ = "elder_profile"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50)
    gender: Optional[int] = Field(default=None)
    birth_date: Optional[date] = Field(default=None)
    phone: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=200)
    emergency_contact: Optional[str] = Field(default=None, max_length=50)
    emergency_phone: Optional[str] = Field(default=None, max_length=20)
    chronic_diseases: Optional[str] = Field(default=None)
    current_medications: Optional[str] = Field(default=None)
    health_summary: Optional[str] = Field(default=None)
    status: int = Field(default=1)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


class FamilyMember(SQLModel, table=True):
    __tablename__ = "family_member"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    elder_id: int
    relation: Optional[str] = Field(default=None, max_length=20)
    is_primary: int = Field(default=0)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


class MedicationSchedule(SQLModel, table=True):
    __tablename__ = "medication_schedule"

    id: Optional[int] = Field(default=None, primary_key=True)
    elder_id: int
    drug_name: str = Field(max_length=100)
    dosage: Optional[str] = Field(default=None, max_length=50)
    schedule_times: str = Field(max_length=100)
    start_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)
    remark: Optional[str] = Field(default=None, max_length=200)
    status: int = Field(default=1)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


class MedicationLog(SQLModel, table=True):
    __tablename__ = "medication_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    schedule_id: int
    elder_id: int
    planned_time: datetime
    taken_time: Optional[datetime] = Field(default=None)
    status: int = Field(default=2)
    create_time: Optional[datetime] = Field(default=None)


class ServiceCatalog(SQLModel, table=True):
    __tablename__ = "service_catalog"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    service_type: str = Field(max_length=50)
    description: Optional[str] = Field(default=None)
    duration_minutes: Optional[int] = Field(default=60)
    status: int = Field(default=1)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


class ServiceBooking(SQLModel, table=True):
    __tablename__ = "service_booking"

    id: Optional[int] = Field(default=None, primary_key=True)
    elder_id: int
    catalog_id: int
    booking_time: datetime
    status: str = Field(default="pending", max_length=20)
    source: str = Field(default="manual", max_length=20)
    remark: Optional[str] = Field(default=None, max_length=200)
    # 有效预约（pending/confirmed）写入；取消/完成后置空，配合 UNIQUE 防并发抢同一时段
    slot_lock: Optional[str] = Field(default=None, max_length=64)
    version: int = Field(default=0)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


class AgentConversation(SQLModel, table=True):
    __tablename__ = "agent_conversation"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    elder_id: Optional[int] = Field(default=None)
    session_id: str = Field(max_length=64)
    role: str = Field(max_length=20)
    content: str
    create_time: Optional[datetime] = Field(default=None)


class AgentToolCallLog(SQLModel, table=True):
    __tablename__ = "agent_tool_call_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(max_length=64)
    conversation_id: Optional[int] = Field(default=None)
    user_id: int
    tool_name: str = Field(max_length=64)
    request_args: Optional[str] = Field(default=None)
    response_data: Optional[str] = Field(default=None)
    status: int = Field(default=1)
    cost_ms: Optional[int] = Field(default=None)
    create_time: Optional[datetime] = Field(default=None)


class CommunityActivity(SQLModel, table=True):
    __tablename__ = "community_activity"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=100)
    content: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None, max_length=200)
    start_time: datetime
    end_time: Optional[datetime] = Field(default=None)
    capacity: Optional[int] = Field(default=None)
    status: int = Field(default=1)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


class ActivityRegistration(SQLModel, table=True):
    __tablename__ = "activity_registration"

    id: Optional[int] = Field(default=None, primary_key=True)
    activity_id: int
    elder_id: int
    user_id: Optional[int] = Field(default=None)
    status: str = Field(default="registered", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


class EmergencyAlert(SQLModel, table=True):
    __tablename__ = "emergency_alert"

    id: Optional[int] = Field(default=None, primary_key=True)
    elder_id: int
    location: Optional[str] = Field(default=None, max_length=200)
    message: Optional[str] = Field(default=None)
    status: str = Field(default="open", max_length=20)
    notify_family: int = Field(default=0)
    notify_staff: int = Field(default=0)
    source: str = Field(default="manual", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


class NotifyInbox(SQLModel, table=True):
    __tablename__ = "notify_inbox"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    elder_id: Optional[int] = Field(default=None)
    title: str = Field(max_length=100)
    content: str
    msg_type: str = Field(default="system", max_length=30)
    source: str = Field(default="system", max_length=20)
    related_id: Optional[int] = Field(default=None)
    is_read: int = Field(default=0)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


class KnowledgeDocument(SQLModel, table=True):
    __tablename__ = "knowledge_document"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    file_path: Optional[str] = Field(default=None, max_length=500)
    doc_type: Optional[str] = Field(default=None, max_length=50)
    status: int = Field(default=0)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


class KnowledgeChunk(SQLModel, table=True):
    __tablename__ = "knowledge_chunk"

    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int
    chunk_index: int
    content: str
    embedding_id: Optional[str] = Field(default=None, max_length=100)
    create_time: Optional[datetime] = Field(default=None)
