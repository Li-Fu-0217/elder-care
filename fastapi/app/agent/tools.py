"""Agent 工具定义：与 elder_service 复用同一套业务逻辑。"""

from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Any, Callable

from sqlmodel import Session

from app.models import AgentToolCallLog, User
from app.schemas.elder import ServiceBookingCreateRequest
from app.schemas.community import EmergencyAlertCreateRequest
from app.services import community_service, elder_service, knowledge_service

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "query_health_record",
            "description": "查询老人健康档案（慢性病、用药摘要、近期漏服）",
            "parameters": {
                "type": "object",
                "properties": {
                    "elder_id": {"type": "integer", "description": "老人ID"},
                },
                "required": ["elder_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_medication_schedule",
            "description": "查询用药计划及近期漏服记录",
            "parameters": {
                "type": "object",
                "properties": {
                    "elder_id": {"type": "integer", "description": "老人ID"},
                },
                "required": ["elder_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_available_service",
            "description": "查询可预约服务时段",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_type": {
                        "type": "string",
                        "description": "health_check / nursing / housekeeping",
                    },
                    "days": {"type": "integer", "description": "未来几天，默认7"},
                },
                "required": ["service_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_service",
            "description": "为老人预约服务（需明确时段）",
            "parameters": {
                "type": "object",
                "properties": {
                    "elder_id": {"type": "integer"},
                    "catalog_id": {"type": "integer"},
                    "booking_time": {
                        "type": "string",
                        "description": "预约时间 YYYY-MM-DD HH:MM 或 ISO",
                    },
                    "remark": {"type": "string"},
                },
                "required": ["elder_id", "catalog_id", "booking_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "notify_family",
            "description": "通知子女（演示级：记录通知内容）",
            "parameters": {
                "type": "object",
                "properties": {
                    "elder_id": {"type": "integer"},
                    "message": {"type": "string"},
                },
                "required": ["elder_id", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_emergency_alert",
            "description": "触发紧急呼叫告警，通知社区工作人员与子女",
            "parameters": {
                "type": "object",
                "properties": {
                    "elder_id": {"type": "integer"},
                    "location": {"type": "string"},
                    "message": {"type": "string"},
                },
                "required": ["elder_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_knowledge_base",
            "description": "检索社区养老政策、用药注意事项等知识库（RAG）",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "用户的知识类问题",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回片段数，默认3",
                    },
                },
                "required": ["question"],
            },
        },
    },
]


def _parse_booking_time(raw: str) -> datetime:
    text = raw.strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return datetime.fromisoformat(raw.replace("Z", "+00:00").replace("T", " ").split("+")[0])


def _to_jsonable(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if isinstance(obj, list):
        return [_to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    return obj


def execute_tool(
    db: Session,
    user: User,
    tool_name: str,
    args: dict[str, Any],
    *,
    session_id: str,
) -> dict[str, Any]:
    start = time.perf_counter()
    status = 1
    try:
        result = _dispatch(db, user, tool_name, args)
        payload = _to_jsonable(result)
    except Exception as exc:  # noqa: BLE001
        status = 0
        payload = {"error": str(exc)}
    cost_ms = int((time.perf_counter() - start) * 1000)
    log = AgentToolCallLog(
        session_id=session_id,
        user_id=user.id or 0,
        tool_name=tool_name,
        request_args=json.dumps(args, ensure_ascii=False),
        response_data=json.dumps(payload, ensure_ascii=False)[:8000],
        status=status,
        cost_ms=cost_ms,
        create_time=datetime.now(),
    )
    db.add(log)
    db.commit()
    return {"ok": status == 1, "data": payload, "cost_ms": cost_ms}


def _dispatch(
    db: Session, user: User, tool_name: str, args: dict[str, Any]
) -> Any:
    handlers: dict[str, Callable[..., Any]] = {
        "query_health_record": _query_health_record,
        "check_medication_schedule": _check_medication_schedule,
        "query_available_service": _query_available_service,
        "book_service": _book_service,
        "notify_family": _notify_family,
        "trigger_emergency_alert": _trigger_emergency_alert,
        "query_knowledge_base": _query_knowledge_base,
    }
    fn = handlers.get(tool_name)
    if fn is None:
        raise ValueError(f"未知工具: {tool_name}")
    return fn(db, user, args)


def _query_health_record(db: Session, user: User, args: dict[str, Any]) -> Any:
    elder_id = int(args["elder_id"])
    return elder_service.get_health(db, elder_id, user)


def _check_medication_schedule(db: Session, user: User, args: dict[str, Any]) -> Any:
    elder_id = int(args["elder_id"])
    schedules = elder_service.list_schedules_for_elder(db, elder_id, user)
    page = elder_service.page_medication_logs(
        db, 1, 20, elder_id, None, user
    )
    missed = [x for x in page.records if x.status == 0][:5]
    return {
        "schedules": schedules,
        "recent_logs": page.records[:10],
        "missed_count": len(missed),
        "missed_logs": missed,
    }


def _query_available_service(db: Session, user: User, args: dict[str, Any]) -> Any:
    service_type = str(args.get("service_type") or "health_check")
    days = int(args.get("days") or 7)
    return elder_service.query_slots(db, service_type, None, days)


def _book_service(db: Session, user: User, args: dict[str, Any]) -> Any:
    body = ServiceBookingCreateRequest(
        elder_id=int(args["elder_id"]),
        catalog_id=int(args["catalog_id"]),
        booking_time=_parse_booking_time(str(args["booking_time"])),
        remark=args.get("remark") or "Agent 预约",
    )
    return elder_service.create_booking(db, body, user, source="agent")


def _notify_family(db: Session, user: User, args: dict[str, Any]) -> Any:
    from app.models import ElderProfile
    from app.services import notify_service

    elder_id = int(args["elder_id"])
    elder_service.assert_family_access(db, user, elder_id)
    message = str(args.get("message") or "").strip()
    if not message:
        message = "智能助手向您发送了一条家庭关怀提醒，请及时查看。"
    elder = db.get(ElderProfile, elder_id)
    elder_name = elder.name if elder else f"老人#{elder_id}"
    title = str(args.get("title") or f"智能提醒：{elder_name}")[:100]
    msg_type = str(args.get("msg_type") or "agent_notify")
    created = notify_service.notify_family_members(
        db,
        elder_id=elder_id,
        title=title,
        content=message,
        msg_type=msg_type,
        source="agent",
    )
    return {
        "notified": True,
        "channel": "inbox",
        "elder_id": elder_id,
        "recipient_count": len(created),
        "message": message,
        "note": f"已向 {len(created)} 位家属发送站内消息",
    }


def _trigger_emergency_alert(db: Session, user: User, args: dict[str, Any]) -> Any:
    body = EmergencyAlertCreateRequest(
        elder_id=int(args["elder_id"]),
        location=args.get("location"),
        message=args.get("message") or "Agent 触发紧急求助",
    )
    return community_service.create_alert(db, body, user, source="agent")


def _query_knowledge_base(db: Session, user: User, args: dict[str, Any]) -> Any:
    question = str(args.get("question") or "").strip()
    if not question:
        raise ValueError("question 不能为空")
    top_k = int(args.get("top_k") or 3)
    result = knowledge_service.query_knowledge(db, question, top_k)
    return result.model_dump(by_alias=True)
