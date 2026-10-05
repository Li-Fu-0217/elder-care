from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.common.result import Result
from app.core.deps import get_current_user, get_db
from app.models import User
from app.schemas import RoleVO
from app.services import menu_service

router = APIRouter(prefix="/roles", tags=["角色"])


@router.get("")
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[list[RoleVO]]:
    return Result.ok(menu_service.list_enabled_roles(db))
