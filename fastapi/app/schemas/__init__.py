from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field, field_validator

from app.common.result import CamelModel


def _empty_str_to_none(v: object) -> object:
    if v is None:
        return None
    if isinstance(v, str) and not v.strip():
        return None
    return v


class UserVO(CamelModel):
    id: int
    username: str
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    status: int
    role: str
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class LoginRequest(CamelModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    captcha_id: str = Field(min_length=1)
    captcha_code: str = Field(min_length=1)

    @field_validator("username")
    @classmethod
    def username_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("用户名不能为空")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_required(cls, v: str) -> str:
        if not v:
            raise ValueError("密码不能为空")
        return v

    @field_validator("captcha_id", "captcha_code")
    @classmethod
    def captcha_required(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("验证码不能为空")
        return str(v).strip()


class CaptchaResponse(CamelModel):
    captcha_id: str
    image_base64: str


class RegisterRequest(CamelModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=3, max_length=50)
    nickname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=20)

    @field_validator("email", mode="before")
    @classmethod
    def email_blank(cls, v: object) -> object:
        return _empty_str_to_none(v)

    @field_validator("username")
    @classmethod
    def username_len(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("用户名不能为空")
        v = v.strip()
        if len(v) < 3 or len(v) > 50:
            raise ValueError("用户名长度为 3～50 个字符")
        return v

    @field_validator("password")
    @classmethod
    def password_len(cls, v: str) -> str:
        if not v:
            raise ValueError("密码不能为空")
        if len(v) < 3 or len(v) > 50:
            raise ValueError("密码长度为 3～50 个字符")
        return v


class LoginResponse(CamelModel):
    token: str
    user: UserVO


class UserSaveRequest(CamelModel):
    id: Optional[int] = None
    username: str = Field(min_length=3, max_length=50)
    password: Optional[str] = Field(default=None, max_length=50)
    nickname: Optional[str] = Field(default=None, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    status: int
    role: str = Field(min_length=1)

    @field_validator("email", mode="before")
    @classmethod
    def email_blank(cls, v: object) -> object:
        return _empty_str_to_none(v)

    @field_validator("username")
    @classmethod
    def username_len(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("用户名不能为空")
        v = v.strip()
        if len(v) < 3 or len(v) > 50:
            raise ValueError("用户名长度为 3～50 个字符")
        return v

    @field_validator("password")
    @classmethod
    def password_len(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if len(v) < 3 or len(v) > 50:
            raise ValueError("密码长度为 3～50 个字符")
        return v

    @field_validator("role")
    @classmethod
    def role_required(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("角色不能为空")
        return v

    @field_validator("status", mode="before")
    @classmethod
    def status_required(cls, v: object) -> object:
        if v is None or v == "":
            raise ValueError("状态不能为空")
        return v

    @field_validator("nickname")
    @classmethod
    def nickname_len(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 50:
            raise ValueError("昵称长度不能超过 50 个字符")
        return v

    @field_validator("phone")
    @classmethod
    def phone_len(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 20:
            raise ValueError("手机号长度不能超过 20 个字符")
        return v


class ProfileUpdateRequest(CamelModel):
    nickname: Optional[str] = Field(default=None, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=20)

    @field_validator("email", mode="before")
    @classmethod
    def email_blank(cls, v: object) -> object:
        return _empty_str_to_none(v)

    @field_validator("nickname")
    @classmethod
    def nickname_len(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 50:
            raise ValueError("昵称长度不能超过 50 个字符")
        return v

    @field_validator("phone")
    @classmethod
    def phone_len(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 20:
            raise ValueError("手机号长度不能超过 20 个字符")
        return v


class AvatarBindRequest(CamelModel):
    path: str = Field(min_length=1)

    @field_validator("path")
    @classmethod
    def path_format(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("头像路径不能为空")
        import re

        if not re.match(r"^/uploads/avatar/[0-9]+_.+", v):
            raise ValueError("头像路径格式不正确")
        return v


class ChangePasswordRequest(CamelModel):
    old_password: str = Field(min_length=1)
    new_password: str = Field(min_length=3, max_length=50)
    confirm_password: str = Field(min_length=1)

    @field_validator("old_password")
    @classmethod
    def old_required(cls, v: str) -> str:
        if not v:
            raise ValueError("原密码不能为空")
        return v

    @field_validator("new_password")
    @classmethod
    def new_len(cls, v: str) -> str:
        if not v:
            raise ValueError("新密码不能为空")
        if len(v) < 3 or len(v) > 50:
            raise ValueError("新密码长度为 3～50 个字符")
        return v

    @field_validator("confirm_password")
    @classmethod
    def confirm_required(cls, v: str) -> str:
        if not v:
            raise ValueError("确认密码不能为空")
        return v


class MenuVO(CamelModel):
    id: int
    parent_id: int
    name: str
    path: str
    icon: Optional[str] = None
    sort_order: int
    roles: str


class MenuSaveRequest(CamelModel):
    id: Optional[int] = None
    parent_id: Optional[int] = 0
    name: str = Field(min_length=1, max_length=50)
    path: str
    icon: Optional[str] = Field(default=None, max_length=50)
    sort_order: Optional[int] = 0
    roles: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("菜单名称不能为空")
        v = v.strip()
        if len(v) > 50:
            raise ValueError("菜单名称长度不能超过 50 个字符")
        return v

    @field_validator("path")
    @classmethod
    def path_format(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("菜单路径不能为空")
        import re

        if not re.match(r"^/admin/[a-zA-Z0-9/_-]+$", v):
            raise ValueError("菜单路径须符合后台路由格式")
        return v


class RoleVO(CamelModel):
    code: str
    name: str


class FileVO(CamelModel):
    path: str
    url: str
    category: str
    original_filename: Optional[str] = None
    size: int


class SystemLogVO(CamelModel):
    id: int
    log_type: str
    log_type_name: str
    username: Optional[str] = None
    module: Optional[str] = None
    action: Optional[str] = None
    method: Optional[str] = None
    url: Optional[str] = None
    ip: Optional[str] = None
    cost_ms: Optional[int] = None
    status: Optional[int] = None
    message: Optional[str] = None
    create_time: Optional[datetime] = None


class IdListRequest(CamelModel):
    ids: list[int] = Field(min_length=1)

    @field_validator("ids")
    @classmethod
    def ids_not_empty(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("请选择要操作的数据")
        return v


class LogBatchDeleteRequest(CamelModel):
    type: str
    ids: list[int] = Field(min_length=1)

    @field_validator("type")
    @classmethod
    def type_valid(cls, v: str) -> str:
        if v not in ("login", "operation"):
            raise ValueError("日志类型须为登录或操作")
        return v

    @field_validator("ids")
    @classmethod
    def ids_not_empty(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("请选择要删除的日志")
        return v
