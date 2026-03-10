from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.core.config import get_settings
from backend.app.core.dependencies import get_emotion_service
from backend.app.schemas.emotion import HealthResponse, StorageInfoResponse
from backend.app.services.emotion_service import EmotionService


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        storage_backend=settings.storage_backend,
        default_user_id=settings.default_user_id,
    )


@router.get("/storage", response_model=StorageInfoResponse)
def get_storage_info(
    service: EmotionService = Depends(get_emotion_service),
) -> StorageInfoResponse:
    return StorageInfoResponse(**service.get_storage_info())
