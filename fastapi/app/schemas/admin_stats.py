from typing import Optional

from app.common.result import CamelModel


class StatCardVO(CamelModel):
    key: str
    label: str
    value: int
    hint: Optional[str] = None


class ChartSeriesVO(CamelModel):
    name: str
    data: list[float | int]


class NamedValueVO(CamelModel):
    name: str
    value: int


class AdminStatsVO(CamelModel):
    cards: list[StatCardVO]
    # 预约状态分布（饼图）
    booking_status: list[NamedValueVO]
    # 各服务类型预约量（柱状）
    booking_by_service: list[NamedValueVO]
    # 近 7 日预约趋势（折线/柱）
    booking_trend_dates: list[str]
    booking_trend_series: list[ChartSeriesVO]
    # Agent 工具调用分布（饼/环）
    tool_usage: list[NamedValueVO]
