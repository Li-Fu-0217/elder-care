"""将 Agent 工具返回整理为面向用户的中文摘要（勿直接展示 JSON）。"""

from __future__ import annotations

import json
from typing import Any


_STATUS = {
    "pending": "待确认",
    "confirmed": "已确认",
    "completed": "已完成",
    "cancelled": "已取消",
    "open": "待处理",
    "handling": "处理中",
    "closed": "已关闭",
}


def format_observation(data: Any, tool_name: str | None = None) -> str:
    parsed = _parse(data)
    if isinstance(parsed, dict) and parsed.get("error"):
        return f"办理未成功：{parsed.get('error')}"

    name = (tool_name or "").strip()
    if name == "book_service" or _looks_like_booking(parsed):
        return _fmt_booking(parsed)
    if name == "notify_family" or _looks_like_notify(parsed):
        return _fmt_notify(parsed)
    if name == "check_medication_schedule" or _looks_like_med(parsed):
        return _fmt_med(parsed)
    if name == "query_health_record" or _looks_like_health(parsed):
        return _fmt_health(parsed)
    if name == "query_available_service" or _looks_like_slots(parsed):
        return _fmt_slots(parsed)
    if name == "trigger_emergency_alert" or _looks_like_alert(parsed):
        return _fmt_alert(parsed)
    if name == "query_knowledge_base" or _looks_like_kb(parsed):
        return _fmt_kb(parsed)

    if isinstance(parsed, str):
        text = parsed.strip()
        if text.startswith("{") or text.startswith("["):
            try:
                return format_observation(json.loads(text), tool_name)
            except json.JSONDecodeError:
                pass
        return text if len(text) <= 280 else text[:280] + "…"

    if isinstance(parsed, list):
        return _fmt_slots(parsed) if parsed else "暂无数据"

    if isinstance(parsed, dict):
        # 兜底：抽取常见中文字段，避免整段 JSON
        parts: list[str] = []
        for key, label in (
            ("catalog_name", "服务"),
            ("catalogName", "服务"),
            ("elder_name", "老人"),
            ("elderName", "老人"),
            ("message", "内容"),
            ("note", "说明"),
        ):
            if parsed.get(key):
                parts.append(f"{label}：{parsed[key]}")
        if parts:
            return "；".join(parts)
        return "已完成该项操作"

    return "已完成该项操作"


def _parse(data: Any) -> Any:
    if isinstance(data, str):
        text = data.strip()
        if (text.startswith("{") and text.endswith("}")) or (
            text.startswith("[") and text.endswith("]")
        ):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return data
        return data
    return data


def _g(d: dict, *keys: str, default: Any = None) -> Any:
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def _fmt_time(raw: Any) -> str:
    if raw is None:
        return ""
    text = str(raw).replace("T", " ")
    return text[:16] if len(text) >= 16 else text


def _looks_like_booking(d: Any) -> bool:
    return isinstance(d, dict) and (
        "booking_time" in d or "bookingTime" in d or "catalog_name" in d or "catalogName" in d
    ) and ("elder_name" in d or "elderName" in d or "catalog_id" in d or "catalogId" in d)


def _fmt_booking(d: Any) -> str:
    if not isinstance(d, dict):
        return "预约已提交"
    name = _g(d, "catalog_name", "catalogName", default="服务")
    elder = _g(d, "elder_name", "elderName", default="")
    when = _fmt_time(_g(d, "booking_time", "bookingTime"))
    status = _STATUS.get(str(_g(d, "status", default="")), str(_g(d, "status", default="")))
    parts = [f"已预约「{name}」"]
    if elder:
        parts.append(f"服务对象：{elder}")
    if when:
        parts.append(f"时间：{when}")
    if status:
        parts.append(f"状态：{status}")
    return "；".join(parts)


def _looks_like_notify(d: Any) -> bool:
    return isinstance(d, dict) and ("notified" in d or "channel" in d) and "message" in d


def _fmt_notify(d: Any) -> str:
    if not isinstance(d, dict):
        return "已通知家属"
    count = d.get("recipient_count")
    msg = str(d.get("message") or "").strip()
    note = str(d.get("note") or "").strip()
    if count is not None:
        head = f"已向 {count} 位家属发送站内消息"
    else:
        head = "已向家属发送站内消息"
    if msg:
        short = msg if len(msg) <= 80 else msg[:80] + "…"
        return f"{head}：{short}"
    if note and "模拟" not in note and "Mock" not in note and "mock" not in note:
        return f"{head}（{note}）"
    return head


def _looks_like_med(d: Any) -> bool:
    return isinstance(d, dict) and (
        "missed_count" in d or "missedCount" in d or "schedules" in d
    )


def _fmt_med(d: Any) -> str:
    if not isinstance(d, dict):
        return "已查询用药情况"
    missed = _g(d, "missed_count", "missedCount", default=0)
    schedules = d.get("schedules") or []
    names: list[str] = []
    for s in schedules[:3]:
        if not isinstance(s, dict):
            continue
        drug = _g(s, "drug_name", "drugName", default="药品")
        times = _g(s, "schedule_times", "scheduleTimes", default="")
        names.append(f"{drug}（{times}）" if times else str(drug))
    plan = "、".join(names) if names else "暂无计划"
    return f"用药计划：{plan}；近三日漏服 {missed} 次"


def _looks_like_health(d: Any) -> bool:
    return isinstance(d, dict) and (
        "chronic_diseases" in d
        or "chronicDiseases" in d
        or "current_medications" in d
        or "currentMedications" in d
        or "health_summary" in d
        or "healthSummary" in d
    )


def _fmt_health(d: Any) -> str:
    if not isinstance(d, dict):
        return "已查询健康档案"
    name = _g(d, "name", "elder_name", "elderName", default="老人")
    diseases = _g(d, "chronic_diseases", "chronicDiseases", default="未登记")
    meds = _g(d, "current_medications", "currentMedications", default="未登记")
    missed = _g(d, "missed_count", "missedCount", default=None)
    text = f"{name}：慢性病 {diseases}；当前用药 {meds}"
    if missed is not None:
        text += f"；近期漏服 {missed} 次"
    return text


def _looks_like_slots(d: Any) -> bool:
    if isinstance(d, list) and d and isinstance(d[0], dict):
        return "slots" in d[0] or "catalog_name" in d[0] or "catalogName" in d[0]
    return isinstance(d, dict) and "slots" in d


def _fmt_slots(d: Any) -> str:
    rows = d if isinstance(d, list) else [d] if isinstance(d, dict) else []
    if not rows:
        return "暂无可预约时段"
    first = rows[0] if isinstance(rows[0], dict) else {}
    catalog = _g(first, "catalog_name", "catalogName", default="服务")
    slots = first.get("slots") or []
    if not slots:
        return f"「{catalog}」暂无可约时段"
    show = [str(s) for s in slots[:4]]
    more = f" 等共 {len(slots)} 个" if len(slots) > 4 else ""
    return f"「{catalog}」可约：{'、'.join(show)}{more}"


def _looks_like_alert(d: Any) -> bool:
    return isinstance(d, dict) and (
        ("status" in d and ("message" in d or "location" in d))
        and ("elder_name" in d or "elderName" in d or "elder_id" in d or "elderId" in d)
    )


def _fmt_alert(d: Any) -> str:
    if not isinstance(d, dict):
        return "已登记紧急求助"
    elder = _g(d, "elder_name", "elderName", default="家人")
    msg = _g(d, "message", default="紧急求助")
    status = _STATUS.get(str(_g(d, "status", default="")), "已登记")
    return f"已为 {elder} 登记紧急求助（{status}）：{msg}"


def _looks_like_kb(d: Any) -> bool:
    return isinstance(d, dict) and (
        "chunks" in d or "hits" in d or "documents" in d or "answer_hint" in d
    )


def _fmt_kb(d: Any) -> str:
    if not isinstance(d, dict):
        return "已检索知识库"
    chunks = d.get("chunks") or d.get("hits") or []
    if isinstance(chunks, list) and chunks:
        first = chunks[0]
        if isinstance(first, dict):
            content = _g(first, "content", "text", default="")
            if content:
                short = content if len(content) <= 100 else content[:100] + "…"
                return f"检索到 {len(chunks)} 条相关说明，例如：{short}"
        return f"检索到 {len(chunks)} 条相关知识"
    return "已检索知识库，可供回答参考"
