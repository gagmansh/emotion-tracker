from __future__ import annotations

from datetime import datetime
from typing import Any

from analytics import (
    calculate_hourly_hq_change,
    calculate_most_common_emotion,
    calculate_weekday_hq_change,
    get_period_range,
    records_to_dataframe,
)
from backend.app.repositories.base import EmotionRepository


PERIOD_LABELS = {
    "today": "오늘",
    "week": "이번 주",
    "month": "이번 달",
    "all": "전체",
}


class EmotionService:
    def __init__(self, repository: EmotionRepository):
        self.repository = repository

    def get_latest_hq(self, user_id: str) -> float:
        return self.repository.get_latest_hq(user_id.strip())

    def save_record(
        self,
        user_id: str,
        emotion: str,
        intensity: int,
        note: str = "",
        recorded_at: datetime | None = None,
    ) -> dict[str, Any]:
        return self._serialize_record(
            self.repository.save_record(
                user_id=user_id.strip(),
                emotion=emotion,
                intensity=intensity,
                note=note,
                recorded_at=recorded_at,
            )
        )

    def list_records(
        self,
        user_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[dict[str, Any]]:
        return [
            self._serialize_record(record)
            for record in self.repository.list_records(
                user_id=user_id.strip(),
                start_at=start_at,
                end_at=end_at,
            )
        ]

    def get_analytics(self, user_id: str, period: str) -> dict[str, Any]:
        normalized_period = period.strip().lower()
        if normalized_period not in PERIOD_LABELS:
            raise ValueError("period는 today, week, month, all 중 하나여야 합니다.")

        localized_period = PERIOD_LABELS[normalized_period]
        start_at, end_at = get_period_range(localized_period)
        records = self.repository.list_records(
            user_id=user_id.strip(),
            start_at=start_at,
            end_at=end_at,
        )
        serialized_records = [self._serialize_record(record) for record in records]
        dataframe = records_to_dataframe(records)

        if dataframe.empty:
            return {
                "user_id": user_id,
                "period": normalized_period,
                "summary": {
                    "record_count": 0,
                    "current_hq": None,
                    "average_hq": None,
                    "average_intensity": None,
                    "most_common_emotion": None,
                },
                "hourly": [],
                "weekday": [],
                "records": serialized_records,
            }

        hourly = calculate_hourly_hq_change(dataframe).to_dict(orient="records")
        weekday = calculate_weekday_hq_change(dataframe).to_dict(orient="records")

        return {
            "user_id": user_id,
            "period": normalized_period,
            "summary": {
                "record_count": len(dataframe),
                "current_hq": round(float(dataframe["HQ_current"].iloc[-1]), 2),
                "average_hq": round(float(dataframe["HQ_current"].mean()), 2),
                "average_intensity": round(float(dataframe["intensity"].mean()), 2),
                "most_common_emotion": calculate_most_common_emotion(dataframe),
            },
            "hourly": hourly,
            "weekday": weekday,
            "records": serialized_records,
        }

    def get_storage_info(self) -> dict[str, Any]:
        return self.repository.get_storage_info()

    @staticmethod
    def _serialize_record(record: dict[str, Any]) -> dict[str, Any]:
        serialized = dict(record)
        timestamp = serialized.get("timestamp")
        if isinstance(timestamp, datetime):
            serialized["timestamp"] = timestamp
        elif isinstance(timestamp, str):
            serialized["timestamp"] = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return serialized
