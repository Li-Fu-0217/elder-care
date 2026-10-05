from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.common.result import Result
from app.core.deps import get_current_user, get_db
from app.models import User
from app.schemas import CaptchaResponse, LoginRequest, LoginResponse, RegisterRequest, UserVO
from app.services import captcha_service, user_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.get("/captcha")
def captcha() -> Result[CaptchaResponse]:
    captcha_id, image_base64 = captcha_service.create_captcha()
    return Result.ok(CaptchaResponse(captcha_id=captcha_id, image_base64=image_base64))


@router.post("/login")
def login(
    body: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Result[LoginResponse]:
    return Result.ok(user_service.login(db, body, request))


@router.post("/register")
def register(
    body: RegisterRequest,
    db: Session = Depends(get_db),
) -> Result[UserVO]:
    return Result.ok(user_service.register(db, body))


@router.get("/me")
def me(current_user: User = Depends(get_current_user)) -> Result[UserVO]:
    return Result.ok(user_service.user_to_vo(current_user))
