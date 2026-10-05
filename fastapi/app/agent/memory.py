"""Agent Memory（长期）：MySQL 会话 → 注入 LangGraph 消息状态。

短时图状态由 LangGraph MemorySaver（thread_id）在 graph.py 中维护。
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from sqlmodel import Session, col, select

from app.models import AgentConversation, User

# 注入图状态的最大历史条数（含本轮用户消息）
MAX_MEMORY_MESSAGES = 20


def load_conversation_memory(
    db: Session,
    user: User,
    session_id: str,
    *,
    elder_id: int,
    current_message: str,
) -> list[BaseMessage]:
    """将落库会话转为 LangChain 消息列表（长期 Memory）。"""
    rows = db.exec(
        select(AgentConversation)
        .where(
            AgentConversation.session_id == session_id,
            AgentConversation.user_id == user.id,
        )
        .order_by(col(AgentConversation.id).asc())
    ).all()

    # 仅取最近 N 条，避免上下文过长
    recent = list(rows[-MAX_MEMORY_MESSAGES:]) if rows else []
    messages: list[BaseMessage] = []
    for i, r in enumerate(recent):
        if r.role not in ("user", "assistant"):
            continue
        is_last_user = (
            i == len(recent) - 1
            and r.role == "user"
            and (r.content or "").strip() == current_message.strip()
        )
        if is_last_user:
            messages.append(
                HumanMessage(content=f"[当前老人ID={elder_id}]\n{current_message}")
            )
        elif r.role == "user":
            messages.append(HumanMessage(content=r.content or ""))
        else:
            messages.append(AIMessage(content=r.content or ""))

    if not messages or not isinstance(messages[-1], HumanMessage):
        messages.append(
            HumanMessage(content=f"[当前老人ID={elder_id}]\n{current_message}")
        )
    return messages


def memory_summary(messages: list[BaseMessage]) -> dict[str, Any]:
    """便于日志与运维排查的 Memory 摘要。"""
    return {
        "messageCount": len(messages),
        "roles": [getattr(m, "type", type(m).__name__) for m in messages],
    }
