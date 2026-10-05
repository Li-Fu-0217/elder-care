"""图形验证码：内存存储，短时有效，一次性校验。"""

from __future__ import annotations

import base64
import io
import random
import string
import threading
import time
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.common.exceptions import BusinessException

_TTL_SECONDS = 300
_CODE_LEN = 4
# 去掉易混淆字符
_ALPHABET = "".join(c for c in string.ascii_uppercase + string.digits if c not in "0O1IL")

_store: dict[str, tuple[str, float]] = {}
_lock = threading.Lock()


def _cleanup_expired(now: float) -> None:
    expired = [k for k, (_, exp) in _store.items() if exp <= now]
    for k in expired:
        _store.pop(k, None)


def _pick_font(size: int = 36) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    ]
    for path in candidates:
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def _render_image(code: str) -> str:
    width, height = 120, 44
    img = Image.new("RGB", (width, height), (245, 247, 250))
    draw = ImageDraw.Draw(img)
    font = _pick_font(32)

    for _ in range(6):
        draw.line(
            (
                random.randint(0, width),
                random.randint(0, height),
                random.randint(0, width),
                random.randint(0, height),
            ),
            fill=(
                random.randint(160, 210),
                random.randint(160, 210),
                random.randint(160, 210),
            ),
            width=1,
        )
    for _ in range(40):
        draw.point(
            (random.randint(0, width - 1), random.randint(0, height - 1)),
            fill=(
                random.randint(120, 200),
                random.randint(120, 200),
                random.randint(120, 200),
            ),
        )

    char_w = width // (len(code) + 1)
    for i, ch in enumerate(code):
        color = (
            random.randint(20, 90),
            random.randint(20, 90),
            random.randint(20, 90),
        )
        x = char_w * (i + 0.4) + random.randint(-2, 2)
        y = random.randint(4, 10)
        draw.text((x, y), ch, font=font, fill=color)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def create_captcha() -> tuple[str, str]:
    code = "".join(random.choices(_ALPHABET, k=_CODE_LEN))
    captcha_id = uuid.uuid4().hex
    image_base64 = _render_image(code)
    now = time.time()
    with _lock:
        _cleanup_expired(now)
        _store[captcha_id] = (code.upper(), now + _TTL_SECONDS)
    return captcha_id, image_base64


def verify_captcha(captcha_id: str | None, captcha_code: str | None) -> None:
    if not captcha_id or not captcha_code or not captcha_code.strip():
        raise BusinessException("请输入验证码")
    now = time.time()
    with _lock:
        _cleanup_expired(now)
        item = _store.pop(captcha_id, None)
    if item is None:
        raise BusinessException("验证码已过期，请刷新后重试")
    expected, _ = item
    if captcha_code.strip().upper() != expected:
        raise BusinessException("验证码错误")
