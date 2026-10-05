from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.models.elder import (
    ActivityRegistration,
    AgentConversation,
    AgentToolCallLog,
    CommunityActivity,
    ElderProfile,
    EmergencyAlert,
    FamilyMember,
    KnowledgeChunk,
    KnowledgeDocument,
    MedicationLog,
    MedicationSchedule,
    NotifyInbox,
    ServiceBooking,
    ServiceCatalog,
)

__all__ = [
    "User",
    "Role",
    "Menu",
    "LoginLog",
    "OperationLog",
    "ElderProfile",
    "FamilyMember",
    "MedicationSchedule",
    "MedicationLog",
    "ServiceCatalog",
    "ServiceBooking",
    "AgentConversation",
    "AgentToolCallLog",
    "CommunityActivity",
    "ActivityRegistration",
    "EmergencyAlert",
    "NotifyInbox",
    "KnowledgeDocument",
    "KnowledgeChunk",
]


class User(SQLModel, table=True):
    __tablename__ = "sys_user"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=50, unique=True, index=True)
    password: str = Field(max_length=100)
    nickname: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    avatar: Optional[str] = Field(default=None, max_length=255)
    status: int = Field(default=1)
    role: str = Field(default="USER", max_length=30)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


class Role(SQLModel, table=True):
    __tablename__ = "sys_role"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(max_length=30, unique=True)
    name: str = Field(max_length=50)
    sort_order: int = Field(default=0)
    status: int = Field(default=1)


class Menu(SQLModel, table=True):
    __tablename__ = "sys_menu"

    id: Optional[int] = Field(default=None, primary_key=True)
    parent_id: int = Field(default=0)
    name: str = Field(max_length=50)
    path: str = Field(max_length=100)
    icon: Optional[str] = Field(default=None, max_length=50)
    sort_order: int = Field(default=0)
    roles: str = Field(default="ADMIN", max_length=100)


class LoginLog(SQLModel, table=True):
    __tablename__ = "sys_login_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=50)
    ip: Optional[str] = Field(default=None, max_length=50)
    status: int
    message: Optional[str] = Field(default=None, max_length=200)
    create_time: Optional[datetime] = Field(default=None)


class OperationLog(SQLModel, table=True):
    __tablename__ = "sys_operation_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: Optional[str] = Field(default=None, max_length=50)
    module: Optional[str] = Field(default=None, max_length=50)
    action: Optional[str] = Field(default=None, max_length=50)
    method: Optional[str] = Field(default=None, max_length=10)
    url: Optional[str] = Field(default=None, max_length=200)
    ip: Optional[str] = Field(default=None, max_length=50)
    cost_ms: Optional[int] = Field(default=None)
    status: int = Field(default=1)
    create_time: Optional[datetime] = Field(default=None)
