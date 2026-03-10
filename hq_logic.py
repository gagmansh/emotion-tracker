from __future__ import annotations

from typing import Final


EMOTION_SCORES: Final[dict[str, float]] = {
    "행복": 9.0,
    "평온": 0.0,
    "슬픔": -7.5,
    "불안": -6.5,
    "분노": -9.0,
}


def clamp_hq(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def calculate_hq(hq_previous: float, emotion: str, intensity: int) -> dict[str, float | str]:
    if emotion not in EMOTION_SCORES:
        available_emotions = ", ".join(EMOTION_SCORES)
        raise ValueError(f"지원하지 않는 감정입니다: {emotion}. 사용 가능 감정: {available_emotions}")

    intensity_value = int(intensity)
    if not 1 <= intensity_value <= 10:
        raise ValueError("강도(intensity)는 1부터 10 사이여야 합니다.")

    normalized_previous = clamp_hq(hq_previous)
    emotion_score = EMOTION_SCORES[emotion]
    delta_hq = emotion_score * (intensity_value / 15)
    adjustment_factor = 1 - abs(normalized_previous - 50) / 100
    adjusted_delta = delta_hq * adjustment_factor
    current_hq = clamp_hq(normalized_previous + adjusted_delta)

    return {
        "emotion": emotion,
        "emotion_score": round(emotion_score, 2),
        "intensity": intensity_value,
        "HQ_previous": round(normalized_previous, 2),
        "HQ_current": round(current_hq, 2),
        "delta_HQ": round(adjusted_delta, 2),
        "adjustment_factor": round(adjustment_factor, 4),
    }
