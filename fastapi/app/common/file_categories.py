AVATAR = "avatar"
COMMON = "common"

SUPPORTED = frozenset({AVATAR, COMMON})


def normalize(category: str | None) -> str:
    if not category or not category.strip():
        return COMMON
    cat = category.strip().lower()
    if cat not in SUPPORTED:
        from app.common.exceptions import BusinessException

        raise BusinessException(f"不支持的上传分类: {category}")
    return cat
