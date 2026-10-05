from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.common.result import Result
from app.core.deps import get_current_user, get_db, operation_log, require_admin
from app.models import User
from app.schemas import MenuSaveRequest, MenuVO
from app.services import menu_service

router = APIRouter(prefix="/menus", tags=["菜单"])


@router.get("")
def my_menus(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[list[MenuVO]]:
    return Result.ok(menu_service.list_menus_for_user(db, current_user.role))


@router.get("/manage")
def manage_list(
    keyword: str | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Result[list[MenuVO]]:
    return Result.ok(menu_service.page_manage(db, keyword))


@router.post("")
@operation_log(module="菜单管理", action="新增菜单")
def create_menu(
    body: MenuSaveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[MenuVO]:
    return Result.ok(menu_service.create_menu(db, body))


@router.put("/{menu_id}")
@operation_log(module="菜单管理", action="修改菜单")
def update_menu(
    menu_id: int,
    body: MenuSaveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[MenuVO]:
    return Result.ok(menu_service.update_menu(db, menu_id, body))


@router.delete("/batch")
@operation_log(module="菜单管理", action="批量删除菜单")
def delete_menus_batch(
    ids: list[int],
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[None]:
    menu_service.delete_menus(db, ids)
    return Result.ok()


@router.delete("/{menu_id}")
@operation_log(module="菜单管理", action="删除菜单")
def delete_menu(
    menu_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[None]:
    menu_service.delete_menu(db, menu_id)
    return Result.ok()
