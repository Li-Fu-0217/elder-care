from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.common.file_categories import AVATAR, normalize
from app.common.result import Result
from app.core.deps import get_current_user, get_db, operation_log
from app.models import User
from app.schemas import FileVO
from app.services import file_service

router = APIRouter(prefix="/files", tags=["文件管理"])


@router.post("/upload")
@operation_log(module="文件管理", action="上传文件")
async def upload(
    request: Request,
    file: UploadFile = File(...),
    category: str = Query("common", description="avatar | common，与前端 params 一致"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[FileVO]:
    cat = normalize(category)
    prefix = str(current_user.id) if cat == AVATAR else None
    vo = await file_service.upload_file(cat, file, prefix)
    return Result.ok(vo)


@router.get("/download")
def download(
    path: str,
    current_user: User = Depends(get_current_user),
):
    local = file_service.load_file_path(path)
    filename = local.name
    encoded = quote(filename)
    return FileResponse(
        path=local,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded}",
        },
    )


@router.get("/preview")
def preview(
    path: str,
    current_user: User = Depends(get_current_user),
):
    local = file_service.load_file_path(path)
    return FileResponse(
        path=local,
        media_type=file_service.probe_media_type(path),
        headers={"Content-Disposition": "inline"},
    )


@router.delete("")
@operation_log(module="文件管理", action="删除文件")
def delete_file(
    path: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Result[None]:
    file_service.delete_for_user(path, current_user.id, current_user.role)  # type: ignore[arg-type]
    return Result.ok()
