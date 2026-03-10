from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from hq_logic import EMOTION_SCORES


class EmotionRecordCreate(BaseModel):
    emotion: str
    intensity: int = Field(ge=1, le=10)
    note: str = ""
    recorded_at: datetime | None = None

    @field_validator("emotion")
    @classmethod
    def validate_emotion(cls, value: str) -> str:
        if value not in EMOTION_SCORES:
            available = ", ".join(EMOTION_SCORES)
            raise ValueError(f"지원하지 않는 감정입니다. 사용 가능 감정: {available}")
        return value


class EmotionRecordResponse(BaseModel):
    id: str
    user_id: str
    timestamp: datetime
    emotion: str
    emotion_score: float
    intensity: int
    HQ_previous: float
    HQ_current: float
    note: str = ""


class CurrentHQResponse(BaseModel):
    user_id: str
    current_hq: float


class StorageInfoResponse(BaseModel):
    backend: str
    storage_path: str | None = None
    firestore_collection: str | None = None
    service_account_path: str | None = None


class HealthResponse(BaseModel):
    status: str
    storage_backend: str
    default_user_id: str
