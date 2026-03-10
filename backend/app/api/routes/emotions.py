from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from backend.app.core.dependencies import get_emotion_service
from backend.app.schemas.analytics import AnalyticsResponse
from backend.app.schemas.emotion import (
    CurrentHQResponse,
    EmotionRecordCreate,
    EmotionRecordResponse,
)
from backend.app.services.emotion_service import EmotionService


router = APIRouter(prefix="/api/v1/users/{user_id}", tags=["emotions"])


@router.get("/hq", response_model=CurrentHQResponse)
def get_current_hq(
    user_id: str,
    service: EmotionService = Depends(get_emotion_service),
) -> CurrentHQResponse:
    return CurrentHQResponse(
        user_id=user_id,
        current_hq=service.get_latest_hq(user_id),
    )


@router.post(
    "/records",
    response_model=EmotionRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_record(
    user_id: str,
    payload: EmotionRecordCreate,
    service: EmotionService = Depends(get_emotion_service),
) -> EmotionRecordResponse:
    return EmotionRecordResponse(
        **service.save_record(
            user_id=user_id,
            emotion=payload.emotion,
            intensity=payload.intensity,
            note=payload.note,
            recorded_at=payload.recorded_at,
        )
    )


@router.get("/records", response_model=list[EmotionRecordResponse])
def list_records(
    user_id: str,
    service: EmotionService = Depends(get_emotion_service),
) -> list[EmotionRecordResponse]:
    return [
        EmotionRecordResponse(**record)
        for record in service.list_records(user_id=user_id)
    ]


@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    user_id: str,
    period: str = Query(default="today", pattern="^(today|week|month|all)$"),
    service: EmotionService = Depends(get_emotion_service),
) -> AnalyticsResponse:
    return AnalyticsResponse(**service.get_analytics(user_id=user_id, period=period))
