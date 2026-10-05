from sqlmodel import Session, col, or_, select

from app.common import menu_paths
from app.common.exceptions import BusinessException
from app.models import Menu, Role
from app.schemas import MenuSaveRequest, MenuVO, RoleVO


def menu_to_vo(menu: Menu) -> MenuVO:
    return MenuVO.model_validate(menu)


def list_menus_for_user(db: Session, role: str) -> list[MenuVO]:
    if role != "ADMIN":
        return []
    stmt = (
        select(Menu)
        .where(col(Menu.path).like("/admin%"))
        .order_by(col(Menu.sort_order), col(Menu.id))
    )
    return [menu_to_vo(m) for m in db.exec(stmt).all()]


def page_manage(
    db: Session, keyword: str | None
) -> list[MenuVO]:
    stmt = select(Menu).where(col(Menu.path).like("/admin%"))
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(
                col(Menu.name).like(kw),
                col(Menu.path).like(kw),
                col(Menu.icon).like(kw),
                col(Menu.roles).like(kw),
            )
        )
    stmt = stmt.order_by(col(Menu.sort_order), col(Menu.id))
    return [menu_to_vo(m) for m in db.exec(stmt).all()]


def _get_or_throw(db: Session, menu_id: int) -> Menu:
    menu = db.get(Menu, menu_id)
    if menu is None:
        raise BusinessException("菜单不存在")
    return menu


def create_menu(db: Session, body: MenuSaveRequest) -> MenuVO:
    path = body.path
    if not path.startswith("/admin/"):
        raise BusinessException("菜单路径须以 /admin/ 开头")
    if path not in menu_paths.ALLOWED:
        raise BusinessException(
            "路径未在白名单中注册，请在后端菜单路径配置与前端路由映射中同步添加"
        )
    parent_id = body.parent_id if body.parent_id is not None else 0
    if parent_id > 0:
        parent = db.get(Menu, parent_id)
        if parent is None:
            raise BusinessException("父菜单不存在")
    exists = db.exec(select(Menu).where(Menu.path == path)).first()
    if exists:
        raise BusinessException("菜单路径已存在")
    icon = body.icon.strip() if body.icon and body.icon.strip() else None
    menu = Menu(
        parent_id=parent_id,
        name=body.name,
        path=path,
        icon=icon,
        sort_order=body.sort_order if body.sort_order is not None else 0,
        roles="ADMIN",
    )
    db.add(menu)
    db.commit()
    db.refresh(menu)
    return menu_to_vo(menu)


def update_menu(db: Session, menu_id: int, body: MenuSaveRequest) -> MenuVO:
    existing = _get_or_throw(db, menu_id)
    path = body.path
    if not path.startswith("/admin/"):
        raise BusinessException("菜单路径须以 /admin/ 开头")
    if path not in menu_paths.ALLOWED:
        raise BusinessException(
            "路径未在白名单中注册，请在后端菜单路径配置与前端路由映射中同步添加"
        )
    if existing.path in menu_paths.PROTECTED and path != existing.path:
        raise BusinessException("内置菜单不可修改路由路径")
    parent_id = body.parent_id if body.parent_id is not None else 0
    if parent_id == menu_id:
        raise BusinessException("父菜单不能是自己")
    if parent_id > 0:
        parent = db.get(Menu, parent_id)
        if parent is None:
            raise BusinessException("父菜单不存在")
    dup = db.exec(
        select(Menu).where(Menu.path == path, Menu.id != menu_id)
    ).first()
    if dup:
        raise BusinessException("菜单路径已存在")
    icon = body.icon.strip() if body.icon and body.icon.strip() else None
    existing.parent_id = parent_id
    existing.name = body.name
    existing.path = path
    existing.icon = icon
    existing.sort_order = body.sort_order if body.sort_order is not None else 0
    existing.roles = "ADMIN"
    db.add(existing)
    db.commit()
    db.refresh(existing)
    return menu_to_vo(existing)


def delete_menu(db: Session, menu_id: int) -> None:
    menu = _get_or_throw(db, menu_id)
    if menu.path in menu_paths.PROTECTED:
        raise BusinessException("内置菜单不可删除")
    child = db.exec(select(Menu).where(Menu.parent_id == menu_id)).first()
    if child:
        raise BusinessException("请先删除子菜单")
    db.delete(menu)
    db.commit()


def delete_menus(db: Session, ids: list[int]) -> None:
    if not ids:
        raise BusinessException("请选择要删除的菜单")
    for mid in dict.fromkeys(ids):
        delete_menu(db, mid)


def list_enabled_roles(db: Session) -> list[RoleVO]:
    stmt = (
        select(Role)
        .where(Role.status == 1)
        .order_by(col(Role.sort_order), col(Role.id))
    )
    return [RoleVO(code=r.code, name=r.name) for r in db.exec(stmt).all()]
