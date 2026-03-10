from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol


class EmotionRepository(Protocol):
    def get_latest_hq(self, user_id: str) -> float:
        ...

    def save_record(
        self,
        user_id: str,
        emotion: str,
        intensity: int,
        note: str = "",
        recorded_at: datetime | None = None,
    ) -> dict[str, Any]:
        ...

    def list_records(
        self,
        user_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[dict[str, Any]]:
        ...

    def get_storage_info(self) -> dict[str, Any]:
        ...
