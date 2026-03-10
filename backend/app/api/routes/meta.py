from __future__ import annotations

from fastapi import APIRouter

from backend.app.schemas.meta import EmotionOption, MetaResponse
from hq_logic import EMOTION_SCORES


router = APIRouter(prefix="/api/v1", tags=["meta"])


@router.get("/meta", response_model=MetaResponse)
def get_meta() -> MetaResponse:
    return MetaResponse(
        emotions=[
            EmotionOption(key=emotion, score=score)
            for emotion, score in EMOTION_SCORES.items()
        ],
        periods=["today", "week", "month", "all"],
    )
