from datetime import datetime

from sqlmodel import Session, col, func, or_, select

from app.common.exceptions import BusinessException
from app.common.file_categories import AVATAR
from app.common.result import PageResult
from app.common.web_utils import client_ip
from app.core.security import create_access_token, hash_password, verify_password
from app.models import LoginLog, Role, User
from app.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    ProfileUpdateRequest,
    RegisterRequest,
    UserSaveRequest,
    UserVO,
)
from app.services import captcha_service
from fastapi import Request


def user_to_vo(user: User) -> UserVO:
    return UserVO.model_validate(user)


def save_login_log(
    db: Session,
    username: str,
    success: bool,
    message: str,
    request: Request | None = None,
) -> None:
    log = LoginLog(
        username=username or "",
        ip=client_ip(request) if request else None,
        status=1 if success else 0,
        message=message,
        create_time=datetime.now(),
    )
    db.add(log)
    db.commit()


def login(db: Session, request_body: LoginRequest, request: Request) -> LoginResponse:
    captcha_service.verify_captcha(request_body.captcha_id, request_body.captcha_code)
    user = db.exec(
        select(User).where(User.username == request_body.username)
    ).first()
    if user is None or not verify_password(request_body.password, user.password):
        save_login_log(db, request_body.username, False, "用户名或密码错误", request)
        raise BusinessException("用户名或密码错误", code=401)
    if user.status != 1:
        save_login_log(db, request_body.username, False, "账号已被禁用", request)
        raise BusinessException("账号已被禁用", code=401)
    token = create_access_token(user.username)
    save_login_log(db, request_body.username, True, "登录成功", request)
    return LoginResponse(token=token, user=user_to_vo(user))


def register(db: Session, body: RegisterRequest) -> UserVO:
    _check_username_unique(db, body.username, None)
    user = User(
        username=body.username,
        password=hash_password(body.password),
        nickname=body.nickname if body.nickname else body.username,
        email=str(body.email) if body.email else None,
        phone=body.phone,
        status=1,
        role="USER",
        create_time=datetime.now(),
        update_time=datetime.now(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_to_vo(user)


def validate_role_code(db: Session, role_code: str) -> None:
    role = db.exec(
        select(Role).where(Role.code == role_code, Role.status == 1)
    ).first()
    if role is None:
        raise BusinessException("角色无效或已禁用")


def _check_username_unique(db: Session, username: str, exclude_id: int | None) -> None:
    stmt = select(User).where(User.username == username)
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    if db.exec(stmt).first() is not None:
        raise BusinessException("用户名已存在")


def _get_user_or_throw(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise BusinessException("用户不存在")
    return user


def _count_active_admins(db: Session) -> int:
    return db.exec(
        select(func.count()).select_from(User).where(User.role == "ADMIN")
    ).one()


def page_users(
    db: Session, current: int, size: int, keyword: str | None
) -> PageResult[UserVO]:
    current = max(1, current)
    size = min(100, max(1, size))
    stmt = select(User)
    count_stmt = select(func.count()).select_from(User)
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        cond = or_(
            col(User.username).like(kw),
            col(User.nickname).like(kw),
            col(User.email).like(kw),
        )
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    total = db.exec(count_stmt).one()
    stmt = (
        stmt.order_by(col(User.create_time).desc())
        .offset((current - 1) * size)
        .limit(size)
    )
    records = [user_to_vo(u) for u in db.exec(stmt).all()]
    return PageResult(records=records, total=total, current=current, size=size)


def get_user_by_id(db: Session, user_id: int) -> UserVO:
    return user_to_vo(_get_user_or_throw(db, user_id))


def create_user(db: Session, body: UserSaveRequest) -> UserVO:
    _check_username_unique(db, body.username, None)
    if not body.password:
        raise BusinessException("密码不能为空")
    validate_role_code(db, body.role)
    user = User(
        username=body.username,
        password=hash_password(body.password),
        nickname=body.nickname,
        email=str(body.email) if body.email else None,
        phone=body.phone,
        status=body.status,
        role=body.role,
        create_time=datetime.now(),
        update_time=datetime.now(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_to_vo(user)


def update_user(db: Session, user_id: int, body: UserSaveRequest) -> UserVO:
    existing = _get_user_or_throw(db, user_id)
    _check_username_unique(db, body.username, user_id)
    validate_role_code(db, body.role)
    if existing.role == "ADMIN" and body.role != "ADMIN" and _count_active_admins(db) <= 1:
        raise BusinessException("至少保留一名管理员")
    existing.username = body.username
    existing.nickname = body.nickname
    existing.email = str(body.email) if body.email else None
    existing.phone = body.phone
    existing.status = body.status
    existing.role = body.role
    if body.password:
        existing.password = hash_password(body.password)
    existing.update_time = datetime.now()
    db.add(existing)
    db.commit()
    db.refresh(existing)
    return user_to_vo(existing)


def delete_user(db: Session, user_id: int, current: User) -> None:
    if current.id == user_id:
        raise BusinessException("不能删除当前登录用户")
    target = _get_user_or_throw(db, user_id)
    if target.role == "ADMIN" and _count_active_admins(db) <= 1:
        raise BusinessException("至少保留一名管理员")
    db.delete(target)
    db.commit()


def delete_users(db: Session, ids: list[int], current: User) -> None:
    if not ids:
        raise BusinessException("请选择要删除的用户")
    for uid in dict.fromkeys(ids):
        delete_user(db, uid, current)


def update_profile(db: Session, current: User, body: ProfileUpdateRequest) -> UserVO:
    user = _get_user_or_throw(db, current.id)  # type: ignore[arg-type]
    user.nickname = body.nickname
    user.email = str(body.email) if body.email else None
    user.phone = body.phone
    user.update_time = datetime.now()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_to_vo(user)


def bind_avatar(db: Session, current: User, path: str, resolve_local, delete_local) -> UserVO:
    prefix = f"/uploads/{AVATAR}/{current.id}_"
    if not path.startswith(prefix):
        raise BusinessException("只能绑定当前用户上传的头像文件")
    resolve_local(path)
    user = _get_user_or_throw(db, current.id)  # type: ignore[arg-type]
    old_path = user.avatar
    user.avatar = path
    user.update_time = datetime.now()
    db.add(user)
    db.commit()
    db.refresh(user)
    if old_path:
        delete_local(old_path)
    return user_to_vo(user)


def change_password(db: Session, current: User, body: ChangePasswordRequest) -> None:
    if body.new_password != body.confirm_password:
        raise BusinessException("两次输入的新密码不一致")
    if body.old_password == body.new_password:
        raise BusinessException("新密码不能与原密码相同")
    user = _get_user_or_throw(db, current.id)  # type: ignore[arg-type]
    if not verify_password(body.old_password, user.password):
        raise BusinessException("原密码错误")
    user.password = hash_password(body.new_password)
    user.update_time = datetime.now()
    db.add(user)
    db.commit()
