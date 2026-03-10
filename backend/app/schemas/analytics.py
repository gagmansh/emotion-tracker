from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from backend.app.schemas.emotion import EmotionRecordResponse


class AnalyticsSummary(BaseModel):
    record_count: int
    current_hq: float | None = None
    average_hq: float | None = None
    average_intensity: float | None = None
    most_common_emotion: str | None = None


class HourlyAnalyticsPoint(BaseModel):
    hour: int
    hour_label: str
    average_hq: float
    record_count: int


class WeekdayAnalyticsPoint(BaseModel):
    weekday_num: int
    weekday: str
    average_hq: float
    record_count: int


class AnalyticsResponse(BaseModel):
    user_id: str
    period: Literal["today", "week", "month", "all"]
    summary: AnalyticsSummary
    hourly: list[HourlyAnalyticsPoint]
    weekday: list[WeekdayAnalyticsPoint]
    records: list[EmotionRecordResponse]
