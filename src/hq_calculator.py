from typing import Dict


# 감정 점수 매핑(요구사항 고정값)
EMOTION_SCORES: Dict[str, float] = {
    "😀 행복": 9.0,
    "😢 슬픔": -7.5,
    "😡 화남": -9.0,
    "😐 평온": 0.0,
    "😰 불안": -6.5,
}


def calculate_hq(hq_previous: float, emotion: str, intensity: int) -> dict:
    """
    HQ 계산 규칙(요구사항):
    - delta_HQ = emotion_score * (intensity / 15)
    - adjustment_factor = 1 - abs(HQ_previous - 50) / 100
    - delta_HQ *= adjustment_factor
    - HQ_current = max(0, min(100, HQ_previous + delta_HQ))
    - 소수 둘째 자리 반올림
    """
    if emotion not in EMOTION_SCORES:
        raise ValueError(f"정의되지 않은 감정입니다: {emotion}")

    if not 1 <= int(intensity) <= 10:
        raise ValueError("강도(intensity)는 1~10 범위여야 합니다.")

    emotion_score = EMOTION_SCORES[emotion]
    delta_hq = emotion_score * (intensity / 15)

    adjustment_factor = 1 - abs(hq_previous - 50) / 100
    delta_hq *= adjustment_factor

    hq_current = max(0.0, min(100.0, hq_previous + delta_hq))

    return {
        "emotion_score": emotion_score,
        "HQ_previous": round(float(hq_previous), 2),
        "HQ_current": round(float(hq_current), 2),
        "delta_HQ": round(float(delta_hq), 2),
        "adjustment_factor": round(float(adjustment_factor), 4),
    }
