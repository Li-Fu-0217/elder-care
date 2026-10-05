from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.common.result import PageResult, Result
from app.core.deps import get_current_user, get_db, operation_log, require_admin
from app.models import User
from app.schemas.elder import (
    ServiceBookingCreateRequest,
    ServiceBookingUpdateRequest,
    ServiceBookingVO,
    ServiceCatalogSaveRequest,
    ServiceCatalogVO,
    ServiceSlotsVO,
)
from app.services import elder_service

router = APIRouter(tags=["服务预约"])


@router.get("/services/catalog")
def list_catalog(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Result[list[ServiceCatalogVO]]:
    return Result.ok(elder_service.list_catalog(db))


@router.get("/admin/services/catalog")
def page_catalog(
    current: int = 1,
    size: int = 50,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Result[PageResult[ServiceCatalogVO]]:
    return Result.ok(elder_service.page_catalog(db, current, size))


@router.post("/admin/services/catalog")
@operation_log(module="服务预约", action="新增服务目录")
def create_catalog(
    body: ServiceCatalogSaveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[ServiceCatalogVO]:
    return Result.ok(elder_service.save_catalog(db, body))


@router.put("/admin/services/catalog/{catalog_id}")
@operation_log(module="服务预约", action="修改服务目录")
def update_catalog(
    catalog_id: int,
    body: ServiceCatalogSaveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[ServiceCatalogVO]:
    return Result.ok(elder_service.save_catalog(db, body, catalog_id))


@router.get("/services/slots")
def query_slots(
    service_type: str | None = None,
    catalog_id: int | None = None,
    days: int = 7,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Result[list[ServiceSlotsVO]]:
    return Result.ok(
        elder_service.query_slots(db, service_type, catalog_id, days)
    )


@router.post("/services/bookings")
@operation_log(module="服务预约", action="创建预约")
def create_booking(
    body: ServiceBookingCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[ServiceBookingVO]:
    return Result.ok(elder_service.create_booking(db, body, current_user))


@router.get("/services/bookings")
def page_my_bookings(
    current: int = 1,
    size: int = 10,
    elder_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[PageResult[ServiceBookingVO]]:
    return Result.ok(
        elder_service.page_bookings(
            db, current, size, elder_id, status, current_user
        )
    )


@router.get("/admin/services/bookings")
def page_admin_bookings(
    current: int = 1,
    size: int = 10,
    elder_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Result[PageResult[ServiceBookingVO]]:
    return Result.ok(
        elder_service.page_bookings(db, current, size, elder_id, status, None)
    )


@router.put("/admin/services/bookings/{booking_id}")
@operation_log(module="服务预约", action="更新预约")
def update_booking(
    booking_id: int,
    body: ServiceBookingUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Result[ServiceBookingVO]:
    return Result.ok(elder_service.update_booking(db, booking_id, body))
