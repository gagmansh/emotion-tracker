from __future__ import annotations

from pydantic import BaseModel


class EmotionOption(BaseModel):
    key: str
    score: float


class MetaResponse(BaseModel):
    emotions: list[EmotionOption]
    periods: list[str]
