"""Agent 入口：演示模式回退 + LangGraph ReAct（真模型路径）。

待确认预约上下文：优先落库（role=pending_book），进程内字典作缓存；
本地单进程 uvicorn 足够；多 worker 时以数据库为准。
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Session, col, select

from app.agent.graph import run_react_agent
from app.agent.tools import execute_tool
from app.core.config import get_settings
from app.models import AgentConversation, User

# 会话内「待用户确认预约」的落库角色（不展示给前端聊天气泡）
_PENDING_ROLE = "pending_book"
# session_id -> 待确认预约上下文（进程内缓存）
_pending_confirm: dict[str, dict[str, Any]] = {}


def _load_pending(
    db: Session, session_id: str, user_id: int
) -> dict[str, Any] | None:
    cached = _pending_confirm.get(session_id)
    if cached is not None:
        return cached
    row = db.exec(
        select(AgentConversation)
        .where(
            AgentConversation.session_id == session_id,
            AgentConversation.user_id == user_id,
            AgentConversation.role == _PENDING_ROLE,
        )
        .order_by(col(AgentConversation.id).desc())
    ).first()
    if not row or not row.content:
        return None
    try:
        data = json.loads(row.content)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict):
        _pending_confirm[session_id] = data
        return data
    return None


def _persist_pending(
    db: Session,
    user: User,
    elder_id: int,
    session_id: str,
    pending: dict[str, Any] | None,
) -> None:
    """写入或清除会话的待确认预约状态。"""
    old_rows = db.exec(
        select(AgentConversation).where(
            AgentConversation.session_id == session_id,
            AgentConversation.user_id == user.id,
            AgentConversation.role == _PENDING_ROLE,
        )
    ).all()
    for row in old_rows:
        db.delete(row)
    if pending:
        db.add(
            AgentConversation(
                user_id=user.id or 0,
                elder_id=elder_id,
                session_id=session_id,
                role=_PENDING_ROLE,
                content=json.dumps(pending, ensure_ascii=False),
                create_time=datetime.now(),
            )
        )
        _pending_confirm[session_id] = pending
    else:
        _pending_confirm.pop(session_id, None)
    db.commit()


def chat(
    db: Session,
    user: User,
    *,
    elder_id: int,
    message: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    sid = session_id or str(uuid.uuid4())
    _save_message(db, user, elder_id, sid, "user", message)

    settings = get_settings()
    use_demo = settings.agent_demo_mode or not (settings.llm_api_key or "").strip()

    if use_demo:
        reply, steps, pending = _run_demo(db, user, elder_id, sid, message)
    else:
        try:
            prior = _load_pending(db, sid, user.id or 0)
            reply, steps, pending = run_react_agent(
                db,
                user,
                elder_id=elder_id,
                session_id=sid,
                message=message,
                prior_pending=prior,
            )
        except Exception as exc:  # noqa: BLE001
            demo_reply, steps, pending = _run_demo(db, user, elder_id, sid, message)
            # 不对用户暴露底层异常细节
            reply = (
                f"{demo_reply}\n"
                "（刚才智能编排暂时不可用，已切换为本地助手继续为您办理。）"
            )
            # 便于服务端排查
            print(f"[agent] langgraph failed, fallback demo: {exc}")

    _save_message(db, user, elder_id, sid, "assistant", reply)
    if pending:
        _persist_pending(db, user, elder_id, sid, pending)
    elif _is_booking_done(steps):
        _persist_pending(db, user, elder_id, sid, None)

    return {
        "sessionId": sid,
        "reply": reply,
        "steps": steps,
        "pendingConfirm": pending,
        "demoMode": use_demo,
        "engine": "demo" if use_demo else "langgraph",
    }


def list_messages(db: Session, user: User, session_id: str) -> list[dict[str, Any]]:
    rows = db.exec(
        select(AgentConversation)
        .where(
            AgentConversation.session_id == session_id,
            AgentConversation.user_id == user.id,
            col(AgentConversation.role).in_(["user", "assistant", "system"]),
        )
        .order_by(col(AgentConversation.id).asc())
    ).all()
    return [
        {
            "id": r.id,
            "role": r.role,
            "content": r.content,
            "createTime": r.create_time,
        }
        for r in rows
    ]


def list_sessions(db: Session, user: User) -> list[dict[str, Any]]:
    rows = db.exec(
        select(AgentConversation)
        .where(
            AgentConversation.user_id == user.id,
            col(AgentConversation.role).in_(["user", "assistant"]),
        )
        .order_by(col(AgentConversation.id).desc())
    ).all()
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for r in rows:
        if r.session_id in seen:
            continue
        seen.add(r.session_id)
        out.append(
            {
                "sessionId": r.session_id,
                "elderId": r.elder_id,
                "preview": r.content[:80],
                "createTime": r.create_time,
            }
        )
        if len(out) >= 20:
            break
    return out


def _save_message(
    db: Session,
    user: User,
    elder_id: int,
    session_id: str,
    role: str,
    content: str,
) -> None:
    row = AgentConversation(
        user_id=user.id or 0,
        elder_id=elder_id,
        session_id=session_id,
        role=role,
        content=content,
        create_time=datetime.now(),
    )
    db.add(row)
    db.commit()


def _is_booking_done(steps: list[dict[str, Any]]) -> bool:
    return any(s.get("action") == "book_service" for s in steps)


def _run_demo(
    db: Session,
    user: User,
    elder_id: int,
    session_id: str,
    message: str,
) -> tuple[str, list[dict[str, Any]], dict[str, Any] | None]:
    steps: list[dict[str, Any]] = []
    text = message.strip()
    pending = _load_pending(db, session_id, user.id or 0)

    # 紧急求助
    if any(k in text for k in ("紧急", "求救", "摔倒", "跌倒", "胸痛", "昏迷", "呼叫120", "急救")):
        steps.append(
            {
                "round": 1,
                "thought": "用户表达紧急情况，立即触发紧急告警",
                "action": "trigger_emergency_alert",
                "observation": "",
            }
        )
        alert_res = execute_tool(
            db,
            user,
            "trigger_emergency_alert",
            {
                "elder_id": elder_id,
                "location": "用户未提供，默认住址",
                "message": text,
            },
            session_id=session_id,
        )
        steps[-1]["observation"] = _brief(alert_res["data"], "trigger_emergency_alert")
        reply = (
            "已触发紧急告警，社区工作人员与家属端将收到站内通知。"
            "如情况危急请同时拨打本地急救电话。"
        )
        return reply, steps, None

    # 知识库问答（政策 / 用药常识）
    need_kb = any(
        k in text
        for k in ("补贴", "政策", "知识", "注意", "怎么吃", "能否", "可以停药", "居家养老")
    ) and not any(k in text for k in ("约", "体检", "漏服", "忘记吃"))
    if need_kb or ("降压药" in text and "约" not in text and "漏" not in text and "忘" not in text):
        steps.append(
            {
                "round": 1,
                "thought": "用户咨询政策/用药常识，检索知识库",
                "action": "query_knowledge_base",
                "observation": "",
            }
        )
        kb = execute_tool(
            db,
            user,
            "query_knowledge_base",
            {"question": text, "top_k": 3},
            session_id=session_id,
        )
        steps[-1]["observation"] = _brief(kb["data"], "query_knowledge_base")
        data = kb.get("data") or {}
        hint = data.get("answerHint") or data.get("answer_hint")
        hits = data.get("hits") or []
        if hint:
            reply = hint
        elif hits:
            reply = "根据知识库：" + "；".join(
                (h.get("content") or "")[:120] for h in hits[:2]
            )
        else:
            reply = "知识库暂未检索到很贴切的内容。您可以换个问法，或咨询社区工作人员 / 医生。"
        return reply, steps, None

    # 用户确认预约
    if pending and _looks_like_confirm(text):
        slot = _match_slot(text, pending.get("options") or [])
        if not slot:
            slot = (pending.get("options") or [None])[0]
        if not slot:
            return (
                "当前没有可确认的预约时段。"
                "您可以稍后再试，或前往「服务中心」手动选择时段预约。",
                steps,
                pending,
            )

        catalog_id = int(pending["catalogId"])
        steps.append(
            {
                "round": 1,
                "thought": "用户已确认预约时段，执行 book_service",
                "action": "book_service",
                "observation": "",
            }
        )
        book_res = execute_tool(
            db,
            user,
            "book_service",
            {
                "elder_id": elder_id,
                "catalog_id": catalog_id,
                "booking_time": slot,
                "remark": "智能助手预约",
            },
            session_id=session_id,
        )
        steps[-1]["observation"] = _brief(book_res["data"], "book_service")
        if not book_res.get("ok"):
            err = ""
            data = book_res.get("data") or {}
            if isinstance(data, dict):
                err = str(data.get("error") or "")
            tip = "该时段可能已被占用或服务暂不可用"
            if "已被预约" in err or "刚被他人" in err:
                tip = "该时段刚被他人预约"
            elif "不存在" in err or "下架" in err:
                tip = "所选服务暂不可用"
            return (
                f"预约未能完成：{tip}。"
                "请换一个时段，或到「服务中心」重新预约。",
                steps,
                pending,
            )

        notify_msg = f"已为家人预约「{pending.get('catalogName', '服务')}」，时间：{slot}"
        steps.append(
            {
                "round": 2,
                "thought": "预约完成，通知子女",
                "action": "notify_family",
                "observation": "",
            }
        )
        notify_res = execute_tool(
            db,
            user,
            "notify_family",
            {"elder_id": elder_id, "message": notify_msg},
            session_id=session_id,
        )
        steps[-1]["observation"] = _brief(notify_res["data"], "notify_family")

        _pending_confirm.pop(session_id, None)
        reply = (
            f"已为您预约成功：{pending.get('catalogName', '服务')}，时间 {slot}。"
            "已通知家属。可在「服务中心」查看预约记录。"
        )
        return reply, steps, None

    need_med = any(k in text for k in ("药", "漏服", "忘记吃", "降压"))
    need_check = any(k in text for k in ("体检", "约", "护理", "家政"))

    if need_med or need_check or not pending:
        round_no = 0
        if need_med or ("健康" in text):
            round_no += 1
            steps.append(
                {
                    "round": round_no,
                    "thought": "用户提到用药/漏服，先查询用药计划与漏服记录",
                    "action": "check_medication_schedule",
                    "observation": "",
                }
            )
            med = execute_tool(
                db,
                user,
                "check_medication_schedule",
                {"elder_id": elder_id},
                session_id=session_id,
            )
            steps[-1]["observation"] = _brief_med(med["data"])

            round_no += 1
            notify_msg = (
                f"智能助手检测到家人近期存在用药漏服风险，"
                f"摘要：{_brief_med(med.get('data'))}。请督促按时服药。"
            )
            steps.append(
                {
                    "round": round_no,
                    "thought": "将漏服情况通知家属，形成智能提醒闭环",
                    "action": "notify_family",
                    "observation": "",
                }
            )
            notify_res = execute_tool(
                db,
                user,
                "notify_family",
                {
                    "elder_id": elder_id,
                    "message": notify_msg,
                    "title": "用药提醒：发现漏服",
                    "msg_type": "medication",
                },
                session_id=session_id,
            )
            steps[-1]["observation"] = _brief(notify_res["data"], "notify_family")

        new_pending = None
        if need_check:
            service_type = "health_check"
            if "护理" in text:
                service_type = "nursing"
            elif "家政" in text:
                service_type = "housekeeping"
            round_no += 1
            steps.append(
                {
                    "round": round_no,
                    "thought": "用户想预约服务，查询可预约时段",
                    "action": "query_available_service",
                    "observation": "",
                }
            )
            slots_res = execute_tool(
                db,
                user,
                "query_available_service",
                {"service_type": service_type, "days": 7},
                session_id=session_id,
            )
            steps[-1]["observation"] = _brief(slots_res["data"], "query_available_service")
            options, catalog_id, catalog_name = _extract_options(slots_res["data"])
            new_pending = {
                "type": "book_service",
                "catalogId": catalog_id,
                "catalogName": catalog_name,
                "options": options[:4],
            }
            round_no += 1
            steps.append(
                {
                    "round": round_no,
                    "thought": "信息已收集，请用户确认预约时间后再执行预约",
                    "action": None,
                    "observation": f"可选时段：{', '.join(options[:4]) or '暂无可约'}",
                }
            )

        reply_parts: list[str] = []
        if need_med:
            med_data = None
            for s in steps:
                if s.get("action") == "check_medication_schedule":
                    med_data = s.get("observation")
                    break
            reply_parts.append(
                f"已查询用药情况：{med_data or '见思考步骤'}。"
                "已向家属发送站内用药提醒，也可在「消息中心」查看；建议到「服药打卡」标记已服。"
            )
        if new_pending and new_pending["options"]:
            opts = "、".join(new_pending["options"])
            reply_parts.append(
                f"本周「{new_pending['catalogName']}」可约时段：{opts}。"
                "请直接回复其中一个时间，或点选下方快捷按钮；也可回复「约第一个」。"
            )
            _pending_confirm[session_id] = new_pending
        elif need_check:
            reply_parts.append(
                "本周暂无可约时段。"
                "您可以稍后再试，前往「服务中心」手动预约，或联系社区工作人员协助安排。"
            )

        if not reply_parts:
            reply_parts.append(
                "我可以帮您查用药漏服、预约体检/护理，或解答养老政策。"
                "例如：「我爸老忘吃降压药，这周想约体检」。"
            )
        return "\n".join(reply_parts), steps, new_pending or pending

    return (
        "请告诉我需要查询用药、预约服务，还是确认刚才给出的预约时段。"
        "不确定时也可以说「查漏服」或「约体检」。",
        steps,
        pending,
    )


def _looks_like_confirm(text: str) -> bool:
    if re.search(r"\d{4}-\d{2}-\d{2}", text):
        return True
    return any(
        k in text
        for k in ("约", "确认", "第一个", "第二个", "周三", "周五", "好的", "可以", "就这个")
    )


def _match_slot(text: str, options: list[str]) -> str | None:
    for opt in options:
        if opt in text or opt.replace(" ", "") in text.replace(" ", ""):
            return opt
    m = re.search(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", text)
    if m:
        return m.group(1)
    if "第一" in text and options:
        return options[0]
    if "第二" in text and len(options) > 1:
        return options[1]
    return None


def _extract_options(data: Any) -> tuple[list[str], int | None, str]:
    if not isinstance(data, list) or not data:
        return [], None, "服务"
    first = data[0] if isinstance(data[0], dict) else {}
    slots = first.get("slots") or []
    return (
        list(slots),
        first.get("catalog_id") or first.get("catalogId"),
        first.get("catalog_name") or first.get("catalogName") or "服务",
    )


from app.agent.observation_format import format_observation


def _brief(data: Any, tool_name: str | None = None) -> str:
    return format_observation(data, tool_name)


def _brief_med(data: Any) -> str:
    return format_observation(data, "check_medication_schedule")
