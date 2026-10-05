"""LangGraph ReAct 编排（主框架）。

配套：LangChain ChatOpenAI / StructuredTool 对接 DeepSeek；Memory 见 memory.py。
"""

from __future__ import annotations

import json
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.agent.memory import load_conversation_memory
from app.agent.observation_format import format_observation
from app.agent.tools import execute_tool
from app.core.config import get_settings
from app.models import User

SYSTEM_PROMPT = """你是社区养老智能助手。根据用户请求自主调用工具完成任务。
可用工具：query_health_record、check_medication_schedule、query_available_service、book_service、notify_family、trigger_emergency_alert、query_knowledge_base。
规则：
1. 涉及用药/漏服先查 check_medication_schedule。
2. 想约体检/护理先 query_available_service，把可选时段告诉用户，等用户确认后再 book_service。
3. 预约成功后可 notify_family。
4. 用户明确求助、跌倒、胸痛、昏迷等紧急情况时调用 trigger_emergency_alert。
5. 涉及养老政策、补贴、用药注意事项等常识问题，先调用 query_knowledge_base 再回答。
6. 回答用简洁中文，不要编造工具未返回的数据。
当前绑定老人ID会在用户消息上下文中给出。"""

# 进程内短时 Memory（按 thread_id=session 保留图状态，配合 MySQL 长期会话）
_checkpointer = MemorySaver()

_NEED_ELDER = frozenset(
    {
        "query_health_record",
        "check_medication_schedule",
        "book_service",
        "notify_family",
        "trigger_emergency_alert",
    }
)


class ElderIdArgs(BaseModel):
    elder_id: int = Field(description="老人ID")


class QueryServiceArgs(BaseModel):
    service_type: str = Field(description="health_check / nursing / housekeeping")
    days: int = Field(default=7, description="未来几天，默认7")


class BookServiceArgs(BaseModel):
    elder_id: int = Field(description="老人ID")
    catalog_id: int = Field(description="服务目录ID")
    booking_time: str = Field(description="预约时间 YYYY-MM-DD HH:MM 或 ISO")
    remark: str = Field(default="Agent 预约", description="备注")


class NotifyFamilyArgs(BaseModel):
    elder_id: int = Field(description="老人ID")
    message: str = Field(description="通知内容")


class EmergencyAlertArgs(BaseModel):
    elder_id: int = Field(description="老人ID")
    location: str | None = Field(default=None, description="位置")
    message: str | None = Field(default=None, description="告警说明")


class KnowledgeQueryArgs(BaseModel):
    question: str = Field(description="用户的知识类问题")
    top_k: int = Field(default=3, description="返回片段数，默认3")


def run_react_agent(
    db: Session,
    user: User,
    *,
    elder_id: int,
    session_id: str,
    message: str,
    prior_pending: dict[str, Any] | None = None,
) -> tuple[str, list[dict[str, Any]], dict[str, Any] | None]:
    """执行一轮 LangGraph ReAct：返回 reply、steps、pendingConfirm。"""
    settings = get_settings()
    base = (settings.llm_base_url or "").rstrip("/")
    if base.endswith("/v1"):
        base = base[:-3]

    extra_body: dict[str, Any] = {
        "thinking": {"type": settings.llm_thinking or "disabled"},
    }
    if (settings.llm_thinking or "disabled") == "enabled":
        extra_body["reasoning_effort"] = settings.llm_reasoning_effort or "high"

    llm_kwargs: dict[str, Any] = {
        "model": settings.llm_model,
        "api_key": settings.llm_api_key,
        "base_url": base or "https://api.deepseek.com",
        "temperature": settings.llm_temperature,
        "extra_body": extra_body,
    }
    if settings.llm_max_tokens:
        llm_kwargs["max_tokens"] = settings.llm_max_tokens
    llm = ChatOpenAI(**llm_kwargs)

    pending_box: dict[str, Any] = {"pending": prior_pending}
    tools = _build_tools(db, user, session_id, elder_id, pending_box)

    agent = create_agent(
        llm,
        tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=_checkpointer,
        name="elder_care_react",
    )

    memory_messages = load_conversation_memory(
        db, user, session_id, elder_id=elder_id, current_message=message
    )
    config = {
        "configurable": {"thread_id": f"u{user.id}:{session_id}"},
        "recursion_limit": 12,
    }

    # 若本线程已有短时图状态，只追加本轮用户消息，避免与 checkpointer 重复堆叠
    state = agent.get_state(config)
    has_checkpoint = bool(state.values.get("messages")) if state and state.values else False
    if has_checkpoint:
        last = (
            memory_messages[-1]
            if memory_messages
            else HumanMessage(content=f"[当前老人ID={elder_id}]\n{message}")
        )
        invoke_input: dict[str, Any] = {"messages": [last]}
    else:
        invoke_input = {"messages": memory_messages}

    result = agent.invoke(invoke_input, config=config)
    result_messages: list[BaseMessage] = list(result.get("messages") or [])
    steps = _extract_steps(result_messages)
    reply = _extract_reply(result_messages)
    return reply, steps, pending_box.get("pending")


def _build_tools(
    db: Session,
    user: User,
    session_id: str,
    default_elder_id: int,
    pending_box: dict[str, Any],
) -> list[StructuredTool]:
    def _call(name: str, args: dict[str, Any]) -> str:
        if "elder_id" not in args and name in _NEED_ELDER:
            args["elder_id"] = default_elder_id
        result = execute_tool(db, user, name, args, session_id=session_id)
        if name == "query_available_service" and result.get("ok"):
            options, catalog_id, catalog_name = _extract_options(result["data"])
            if options:
                pending_box["pending"] = {
                    "type": "book_service",
                    "catalogId": catalog_id,
                    "catalogName": catalog_name,
                    "options": options[:4],
                }
        return json.dumps(result["data"], ensure_ascii=False, default=str)[:6000]

    return [
        StructuredTool.from_function(
            name="query_health_record",
            description="查询老人健康档案（慢性病、用药摘要、近期漏服）",
            func=lambda elder_id: _call("query_health_record", {"elder_id": elder_id}),
            args_schema=ElderIdArgs,
        ),
        StructuredTool.from_function(
            name="check_medication_schedule",
            description="查询用药计划及近期漏服记录",
            func=lambda elder_id: _call(
                "check_medication_schedule", {"elder_id": elder_id}
            ),
            args_schema=ElderIdArgs,
        ),
        StructuredTool.from_function(
            name="query_available_service",
            description="查询可预约服务时段",
            func=lambda service_type, days=7: _call(
                "query_available_service",
                {"service_type": service_type, "days": days},
            ),
            args_schema=QueryServiceArgs,
        ),
        StructuredTool.from_function(
            name="book_service",
            description="为老人预约服务（需明确时段）",
            func=lambda elder_id, catalog_id, booking_time, remark="Agent 预约": _call(
                "book_service",
                {
                    "elder_id": elder_id,
                    "catalog_id": catalog_id,
                    "booking_time": booking_time,
                    "remark": remark,
                },
            ),
            args_schema=BookServiceArgs,
        ),
        StructuredTool.from_function(
            name="notify_family",
            description="通知子女（演示级：记录通知内容）",
            func=lambda elder_id, message: _call(
                "notify_family", {"elder_id": elder_id, "message": message}
            ),
            args_schema=NotifyFamilyArgs,
        ),
        StructuredTool.from_function(
            name="trigger_emergency_alert",
            description="触发紧急呼叫告警，通知社区工作人员与子女",
            func=lambda elder_id, location=None, message=None: _call(
                "trigger_emergency_alert",
                {
                    "elder_id": elder_id,
                    "location": location,
                    "message": message,
                },
            ),
            args_schema=EmergencyAlertArgs,
        ),
        StructuredTool.from_function(
            name="query_knowledge_base",
            description="检索社区养老政策、用药注意事项等知识库（RAG）",
            func=lambda question, top_k=3: _call(
                "query_knowledge_base",
                {"question": question, "top_k": top_k},
            ),
            args_schema=KnowledgeQueryArgs,
        ),
    ]


def _extract_steps(messages: list[BaseMessage]) -> list[dict[str, Any]]:
    """从 LangGraph 消息轨迹还原前端思考步骤。"""
    steps: list[dict[str, Any]] = []
    round_no = 0
    # 只解析本轮新增部分：从最后一条 HumanMessage 之后开始
    start = 0
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].__class__.__name__ == "HumanMessage":
            start = i + 1
            break
    for msg in messages[start:]:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            thought = (msg.content or "").strip() if isinstance(msg.content, str) else ""
            for tc in msg.tool_calls:
                round_no += 1
                name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "")
                steps.append(
                    {
                        "round": round_no,
                        "thought": thought or f"调用工具 {name}",
                        "action": name,
                        "observation": "",
                    }
                )
        elif isinstance(msg, ToolMessage):
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            tool_name = getattr(msg, "name", None) or ""
            brief = format_observation(content, tool_name)
            for s in reversed(steps):
                if s.get("action") == tool_name and not s.get("observation"):
                    s["observation"] = brief
                    break
            else:
                if steps and not steps[-1].get("observation"):
                    steps[-1]["observation"] = brief
        elif isinstance(msg, AIMessage) and (msg.content or "") and not msg.tool_calls:
            round_no += 1
            steps.append(
                {
                    "round": round_no,
                    "thought": "整理答复给您",
                    "action": None,
                    "observation": "已生成办理结果说明",
                }
            )
    return steps


def _extract_reply(messages: list[BaseMessage]) -> str:
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and not msg.tool_calls:
            content = msg.content
            if isinstance(content, str) and content.strip():
                return content.strip()
            if content:
                return str(content)
    return "已处理完成。"


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
