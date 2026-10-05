from collections.abc import Callable
from datetime import datetime
from functools import wraps
import inspect
import time
from typing import Any

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from app.common.exceptions import BusinessException
from app.core.security import parse_username_from_token
from app.db.session import get_session
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_db(session: Session = Depends(get_session)) -> Session:
    return session


def _load_active_user(db: Session, username: str) -> User | None:
    user = db.exec(select(User).where(User.username == username)).first()
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise BusinessException("未登录或登录已过期", code=401)
    username = parse_username_from_token(credentials.credentials)
    if not username:
        raise BusinessException("未登录或登录已过期", code=401)
    user = _load_active_user(db, username)
    if user is None:
        raise BusinessException("未登录或登录已过期", code=401)
    if user.status != 1:
        raise BusinessException("账号已被禁用", code=401)
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "ADMIN":
        raise BusinessException("无权限访问", code=403)
    return current_user


def _persist_operation_log(
    db: Session | None,
    request: Request | None,
    user: User | None,
    module: str,
    action: str,
    status: int,
    start: float,
) -> None:
    if db is None or request is None:
        return
    from app.common.web_utils import client_ip
    from app.models import OperationLog

    try:
        log = OperationLog(
            username=user.username if user else "匿名",
            module=module,
            action=action,
            method=request.method,
            url=str(request.url.path),
            ip=client_ip(request),
            cost_ms=int((time.perf_counter() - start) * 1000),
            status=status,
            create_time=datetime.now(),
        )
        if status == 0:
            db.rollback()
        db.add(log)
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass


def operation_log(module: str, action: str) -> Callable:
    """写操作日志；同步 / 异步路由均可。被装饰路由须注入 request、db。"""

    def decorator(fn: Callable) -> Callable:
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                request: Request | None = kwargs.get("request")
                db: Session | None = kwargs.get("db")
                user: User | None = kwargs.get("current_user") or kwargs.get("admin")
                start = time.perf_counter()
                status = 1
                act = action
                try:
                    return await fn(*args, **kwargs)
                except Exception:
                    status = 0
                    act = f"{action}（失败）"
                    raise
                finally:
                    _persist_operation_log(db, request, user, module, act, status, start)

            return async_wrapper

        @wraps(fn)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            request: Request | None = kwargs.get("request")
            db: Session | None = kwargs.get("db")
            user: User | None = kwargs.get("current_user") or kwargs.get("admin")
            start = time.perf_counter()
            status = 1
            act = action
            try:
                return fn(*args, **kwargs)
            except Exception:
                status = 0
                act = f"{action}（失败）"
                raise
            finally:
                _persist_operation_log(db, request, user, module, act, status, start)

        return sync_wrapper

    return decorator
