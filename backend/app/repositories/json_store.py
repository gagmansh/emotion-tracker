from __future__ import annotations

from datetime import datetime
from typing import Any

from firebase_utils import (
    fetch_emotion_records,
    get_latest_hq,
    get_storage_path,
    initialize_local_store,
    save_emotion_record,
)


class JsonEmotionRepository:
    def __init__(self, storage_path: str):
        self.storage_path = initialize_local_store(storage_path)

    def get_latest_hq(self, user_id: str) -> float:
        return get_latest_hq(self.storage_path, user_id)

    def save_record(
        self,
        user_id: str,
        emotion: str,
        intensity: int,
        note: str = "",
        recorded_at: datetime | None = None,
    ) -> dict[str, Any]:
        return save_emotion_record(
            storage_path=self.storage_path,
            user_id=user_id,
            emotion=emotion,
            intensity=intensity,
            note=note,
            recorded_at=recorded_at,
        )

    def list_records(
        self,
        user_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[dict[str, Any]]:
        return fetch_emotion_records(
            storage_path=self.storage_path,
            user_id=user_id,
            start_at=start_at,
            end_at=end_at,
        )

    def get_storage_info(self) -> dict[str, Any]:
        return {
            "backend": "json",
            "storage_path": str(get_storage_path(str(self.storage_path))),
        }
