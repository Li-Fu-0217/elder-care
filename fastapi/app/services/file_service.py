import mimetypes
import time
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.common.exceptions import BusinessException
from app.common.file_categories import AVATAR, COMMON, normalize
from app.core.config import get_settings
from app.schemas import FileVO

PUBLIC_PREFIX = "/uploads/"

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
COMMON_EXT = IMAGE_EXT | {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".zip",
    ".rar",
    ".txt",
}


def _upload_root() -> Path:
    root = get_settings().upload_root
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_local_path(access_path: str) -> Path:
    if not access_path or not access_path.startswith(PUBLIC_PREFIX):
        raise BusinessException("无效的文件路径")
    relative = access_path[len(PUBLIC_PREFIX) :]
    root = _upload_root()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise BusinessException("无效的文件路径") from exc
    return path


def _resolve_extension(
    filename: str | None, content_type: str | None, allowed: set[str]
) -> str | None:
    ext = ""
    if filename and "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()
    if ext in allowed:
        return ".jpg" if ext == ".jpeg" else ext
    if content_type:
        guessed = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ""
        if guessed == ".jpe":
            guessed = ".jpg"
        if guessed in allowed or (guessed == ".jpeg" and ".jpg" in allowed):
            return ".jpg" if guessed in {".jpeg", ".jpe"} else guessed
    return None


async def upload_file(
    category: str | None,
    file: UploadFile,
    filename_prefix: str | None = None,
) -> FileVO:
    cat = normalize(category)
    if file is None or not file.filename:
        raise BusinessException("请选择文件")

    if cat == AVATAR:
        max_bytes = 2 * 1024 * 1024
        allowed = IMAGE_EXT
    else:
        max_bytes = 10 * 1024 * 1024
        allowed = COMMON_EXT

    content = await file.read()
    if not content:
        raise BusinessException("请选择文件")
    if len(content) > max_bytes:
        raise BusinessException(f"文件大小不能超过 {max_bytes // 1024 // 1024}MB")

    ext = _resolve_extension(file.filename, file.content_type, allowed)
    if not ext:
        raise BusinessException("不支持的文件类型")

    if filename_prefix:
        base_name = f"{filename_prefix}_{int(time.time() * 1000)}"
    else:
        base_name = uuid.uuid4().hex
    filename = base_name + ext

    dir_path = _upload_root() / cat
    dir_path.mkdir(parents=True, exist_ok=True)
    target = dir_path / filename
    target.write_bytes(content)

    access_path = f"{PUBLIC_PREFIX}{cat}/{filename}"
    return FileVO(
        path=access_path,
        url=access_path,
        category=cat,
        original_filename=file.filename,
        size=len(content),
    )


def load_file_path(access_path: str) -> Path:
    path = resolve_local_path(access_path)
    if not path.exists() or not path.is_file():
        raise BusinessException("文件不存在", code=404)
    return path


def delete_local_file(access_path: str | None) -> None:
    if not access_path or not access_path.startswith(PUBLIC_PREFIX):
        return
    try:
        path = resolve_local_path(access_path)
        path.unlink(missing_ok=True)
    except BusinessException:
        pass
    except OSError:
        pass


def delete_for_user(access_path: str, user_id: int, role: str) -> None:
    resolve_local_path(access_path)
    avatar_prefix = f"{PUBLIC_PREFIX}{AVATAR}/{user_id}_"
    if access_path.startswith(avatar_prefix):
        delete_local_file(access_path)
        return
    if access_path.startswith(f"{PUBLIC_PREFIX}{COMMON}/"):
        if role != "ADMIN":
            raise BusinessException("需要管理员权限", code=403)
        delete_local_file(access_path)
        return
    raise BusinessException("只能删除本人头像或管理员删除通用附件")


def probe_media_type(path: str) -> str:
    lower = (path or "").lower()
    if lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".gif"):
        return "image/gif"
    if lower.endswith(".webp"):
        return "image/webp"
    if lower.endswith(".pdf"):
        return "application/pdf"
    if lower.endswith(".txt"):
        return "text/plain"
    return "application/octet-stream"
