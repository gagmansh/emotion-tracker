from __future__ import annotations

from functools import lru_cache

from backend.app.core.config import get_settings
from backend.app.repositories.base import EmotionRepository
from backend.app.repositories.firestore_store import FirestoreEmotionRepository
from backend.app.repositories.json_store import JsonEmotionRepository
from backend.app.services.emotion_service import EmotionService


@lru_cache(maxsize=1)
def get_repository() -> EmotionRepository:
    settings = get_settings()

    if settings.storage_backend == "json":
        return JsonEmotionRepository(settings.local_data_path)

    if settings.storage_backend == "firestore":
        return FirestoreEmotionRepository(
            service_account_path=settings.firebase_service_account_path,
            service_account_json=settings.firebase_service_account_json,
            collection_name=settings.firestore_collection_name,
        )

    raise RuntimeError(
        "지원하지 않는 APP_STORAGE_BACKEND입니다. "
        "사용 가능한 값: json, firestore"
    )


@lru_cache(maxsize=1)
def get_emotion_service() -> EmotionService:
    return EmotionService(get_repository())
