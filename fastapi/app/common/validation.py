"""将 Pydantic / FastAPI 校验错误转为纯中文提示（不暴露英文字段名与 Value error 前缀）。"""

from __future__ import annotations

FIELD_LABELS: dict[str, str] = {
    "username": "用户名",
    "password": "密码",
    "nickname": "昵称",
    "email": "邮箱",
    "phone": "手机号",
    "role": "角色",
    "status": "状态",
    "old_password": "原密码",
    "oldPassword": "原密码",
    "new_password": "新密码",
    "newPassword": "新密码",
    "confirm_password": "确认密码",
    "confirmPassword": "确认密码",
    "path": "文件路径",
    "name": "名称",
    "icon": "图标",
    "parent_id": "父菜单",
    "parentId": "父菜单",
    "sort_order": "排序",
    "sortOrder": "排序",
    "ids": "选中项",
    "type": "类型",
    "file": "文件",
    "category": "分类",
    "keyword": "关键字",
    "current": "页码",
    "size": "每页条数",
}


def _field_label(loc: tuple | list) -> str | None:
    parts = [str(x) for x in loc if x not in ("body", "query", "path", "header", "cookie")]
    if not parts:
        return None
    key = parts[-1]
    if key.isdigit():
        return None
    return FIELD_LABELS.get(key, None)


def _strip_value_error_prefix(msg: str) -> str:
    for prefix in ("Value error, ", "Assertion failed, ", "Value error:", "Assertion failed:"):
        if msg.startswith(prefix):
            return msg[len(prefix) :].strip()
    return msg


def _translate_msg(err: dict) -> str:
    err_type = err.get("type") or ""
    msg = _strip_value_error_prefix(str(err.get("msg") or "参数错误"))
    ctx = err.get("ctx") or {}
    label = _field_label(err.get("loc") or ())

    # 自定义 ValueError 已是中文时直接返回
    if err_type == "value_error" and msg and not msg[:1].isascii():
        return msg
    if msg and not any(c.isascii() and c.isalpha() for c in msg):
        # 几乎全是中文/数字/标点
        return msg

    if err_type in ("missing", "value_error.missing"):
        return f"{label}不能为空" if label else "必填项不能为空"

    if err_type == "string_too_short":
        min_len = ctx.get("min_length")
        if label and min_len is not None:
            return f"{label}长度不能少于 {min_len} 个字符"
        return f"{label}长度过短" if label else "长度过短"

    if err_type == "string_too_long":
        max_len = ctx.get("max_length")
        if label and max_len is not None:
            return f"{label}长度不能超过 {max_len} 个字符"
        return f"{label}长度过长" if label else "长度过长"

    if err_type in ("string_pattern_mismatch", "string_type"):
        return f"{label}格式不正确" if label else "格式不正确"

    if err_type in (
        "value_error.email",
        "value_error",
    ) and "email" in msg.lower():
        return "邮箱格式不正确"

    if "email" in err_type or "email" in msg.lower():
        return "邮箱格式不正确"

    if err_type in ("int_parsing", "int_type", "float_parsing", "float_type"):
        return f"{label}须为数字" if label else "须为数字"

    if err_type in ("bool_parsing", "bool_type"):
        return f"{label}须为布尔值" if label else "须为布尔值"

    if err_type == "list_type":
        return f"{label}格式不正确" if label else "列表格式不正确"

    if err_type == "too_short":
        return f"{label}不能为空" if label else "不能为空"

    # 仍含英文时尽量给出通用中文
    if any(c.isalpha() and c.isascii() for c in msg):
        return f"{label}参数不正确" if label else "参数不正确"

    return msg


def format_validation_errors(errors: list[dict]) -> str:
    messages: list[str] = []
    seen: set[str] = set()
    for err in errors:
        text = _translate_msg(err).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        messages.append(text)
    return "；".join(messages) if messages else "参数校验失败"
