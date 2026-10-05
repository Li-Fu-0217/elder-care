"""Agent 工具目录：用途、入参与使用规则（管理端说明页数据源）。

与 tools.TOOL_DEFINITIONS / execute_tool 保持一致，供运维与产品说明对照。
"""

from __future__ import annotations

from typing import Any


TOOL_CATALOG: list[dict[str, Any]] = [
    {
        "name": "query_health_record",
        "label": "查询健康档案",
        "category": "查询",
        "sideEffect": "只读",
        "summary": "读取老人档案中的慢性病、当前用药摘要，并附带近期漏服概况。",
        "params": [
            {"name": "elder_id", "type": "integer", "required": True, "desc": "老人档案 ID"},
        ],
        "rules": [
            "调用前须已选定服务对象老人；USER 仅能查询本人已绑定的老人。",
            "用于回答「身体怎么样」「有什么慢性病」「最近有没有漏吃药」等概况问题。",
            "不替代医院诊断；涉及改药、停药须引导家属咨询医生。",
            "每次调用会写入 agent_tool_call_log，便于管理端审计。",
        ],
        "examples": ["查一下张建国的健康档案", "老人有什么慢性病和用药"],
    },
    {
        "name": "check_medication_schedule",
        "label": "查询用药与漏服",
        "category": "查询",
        "sideEffect": "只读",
        "summary": "查询启用中的用药计划，并统计近几日漏服（status=0）记录。",
        "params": [
            {"name": "elder_id", "type": "integer", "required": True, "desc": "老人档案 ID"},
        ],
        "rules": [
            "适合「忘吃药」「漏服」「降压药吃了没」等意图，常作为预约链路的第一步。",
            "漏服判定来自 medication_log，不是实时传感器；以系统打卡数据为准。",
            "发现漏服后，演示编排通常会继续调用 notify_family 提醒子女。",
            "USER 只能查已绑定老人；标记已服请走前台「服药打卡」，本工具不改写记录。",
        ],
        "examples": ["我爸最近老忘记吃降压药", "查一下近三天有没有漏服"],
    },
    {
        "name": "query_available_service",
        "label": "查询可预约时段",
        "category": "查询",
        "sideEffect": "只读",
        "summary": "按服务类型（体检/护理/家政）列出未来若干天尚未被占用的可约时段。",
        "params": [
            {
                "name": "service_type",
                "type": "string",
                "required": True,
                "desc": "health_check | nursing | housekeeping",
            },
            {
                "name": "days",
                "type": "integer",
                "required": False,
                "desc": "向前查看天数，默认 7",
            },
        ],
        "rules": [
            "须指定服务类型；不要在未查时段前直接 book_service。",
            "返回的时段已排除 pending/confirmed 占用；取消/完成后的时段可再约。",
            "演示流程：查出时段后进入「待用户确认」，用户选定时间后再预约。",
            "若无可约时段，应提示改日或前往「服务中心」人工办理。",
        ],
        "examples": ["这周想约个体检", "有没有上门护理的空档"],
    },
    {
        "name": "book_service",
        "label": "提交服务预约",
        "category": "办理",
        "sideEffect": "写库",
        "summary": "为指定老人写入一条服务预约，来源标记为 agent。",
        "params": [
            {"name": "elder_id", "type": "integer", "required": True, "desc": "老人档案 ID"},
            {"name": "catalog_id", "type": "integer", "required": True, "desc": "服务目录 ID"},
            {
                "name": "booking_time",
                "type": "string",
                "required": True,
                "desc": "YYYY-MM-DD HH:MM 或 ISO 时间",
            },
            {"name": "remark", "type": "string", "required": False, "desc": "备注"},
        ],
        "rules": [
            "必须在用户明确确认时段之后调用；禁止擅自挑选时间落库。",
            "catalog_id 与 booking_time 须来自 query_available_service 的有效结果。",
            "并发防重：写入 slot_lock 唯一键 + version 乐观锁，冲突时提示换时段。",
            "成功后 source=agent，可在「服务中心 / 管理端预约」复核；常再调 notify_family。",
        ],
        "examples": ["就约明天上午 9 点体检", "确认预约第一个时段"],
    },
    {
        "name": "notify_family",
        "label": "通知子女",
        "category": "通知",
        "sideEffect": "写库",
        "summary": "向该老人绑定的家属发送站内消息（写入消息中心收件箱）。",
        "params": [
            {"name": "elder_id", "type": "integer", "required": True, "desc": "老人档案 ID"},
            {"name": "message", "type": "string", "required": True, "desc": "通知正文"},
        ],
        "rules": [
            "一期仅站内消息，不做微信/短信/App 推送；文案中勿承诺「已发短信」。",
            "每位老人当前仅一位主家属；无绑定时通知数为 0，应提示先完成家属绑定。",
            "适用于漏服提醒、预约成功、健康关怀等场景；紧急情况优先用 trigger_emergency_alert。",
            "消息可在前台顶栏铃铛「消息中心」查看。",
        ],
        "examples": ["提醒家属督促吃药", "预约成功后通知子女"],
    },
    {
        "name": "trigger_emergency_alert",
        "label": "紧急告警",
        "category": "告警",
        "sideEffect": "写库",
        "summary": "创建紧急呼叫工单，并同步站内消息通知家属与社区侧处理。",
        "params": [
            {"name": "elder_id", "type": "integer", "required": True, "desc": "老人档案 ID"},
            {"name": "location", "type": "string", "required": False, "desc": "位置描述"},
            {"name": "message", "type": "string", "required": False, "desc": "告警说明"},
        ],
        "rules": [
            "仅在跌倒、胸痛、昏迷、明确求救等紧急意图时调用。",
            "同时应口头/文案提醒用户必要时拨打 120；本工具不能替代急救。",
            "写入 emergency_alert（默认 open），管理端「紧急告警」可改状态。",
            "会同步站内消息；无家属绑定时仍保留告警工单供社区处理。",
        ],
        "examples": ["老人摔倒了快帮忙", "紧急呼叫，疑似胸痛"],
    },
    {
        "name": "query_knowledge_base",
        "label": "检索知识库",
        "category": "知识",
        "sideEffect": "只读",
        "summary": "对政策/用药/服务类文档做 RAG 检索（MySQL 切片 + Chroma 向量）。",
        "params": [
            {"name": "question", "type": "string", "required": True, "desc": "用户的知识类问题"},
            {
                "name": "top_k",
                "type": "integer",
                "required": False,
                "desc": "返回片段数，默认 3",
            },
        ],
        "rules": [
            "适合补贴政策、用药注意事项、服务办理指引等「有据可查」的问题。",
            "回答应基于检索片段，避免编造未入库政策；片段不足时如实说明。",
            "知识库由管理端上传 txt/md/pdf 并向量化；文档未就绪时可能无命中。",
            "医疗决策仍须遵医嘱；知识库仅作社区服务与用药常识参考。",
        ],
        "examples": ["居家养老补贴怎么申请", "降压药漏服了怎么办"],
    },
]


def list_tool_catalog() -> list[dict[str, Any]]:
    """返回全部工具说明（只读）。"""
    return list(TOOL_CATALOG)


def get_tool_catalog_item(name: str) -> dict[str, Any] | None:
    key = (name or "").strip()
    for item in TOOL_CATALOG:
        if item["name"] == key:
            return item
    return None
