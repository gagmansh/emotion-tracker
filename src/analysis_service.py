from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import pandas as pd


# 날짜 필터 옵션(요구사항 고정)
PERIOD_OPTIONS = ["오늘", "이번 주", "이번 달"]


def get_period_range_utc(period: str) -> Tuple[datetime, datetime]:
    """
    사용자가 고른 기간(오늘/이번 주/이번 달)을 UTC 범위로 변환한다.
    - 저장 시각은 UTC 기준
    - UI 기준 시각은 로컬 타임존 기준
    """
    now_local = datetime.now().astimezone()
    start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "오늘":
        pass
    elif period == "이번 주":
        start_local = start_local - timedelta(days=start_local.weekday())
    elif period == "이번 달":
        start_local = start_local.replace(day=1)
    else:
        raise ValueError(f"지원하지 않는 기간 필터입니다: {period}")

    return start_local.astimezone(timezone.utc), now_local.astimezone(timezone.utc)


def records_to_dataframe(records: list) -> pd.DataFrame:
    """Firestore 조회 결과를 분석용 DataFrame으로 변환한다."""
    base_columns = [
        "timestamp",
        "emotion",
        "emotion_score",
        "intensity",
        "HQ_previous",
        "HQ_current",
        "user_id",
    ]

    if not records:
        return pd.DataFrame(columns=base_columns)

    df = pd.DataFrame(records)
    local_tz = datetime.now().astimezone().tzinfo

    # timestamp를 안전하게 datetime으로 변환하고 로컬 시간대로 맞춘다.
    ts_utc = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df["timestamp_local"] = ts_utc.dt.tz_convert(local_tz)
    df["timestamp_str"] = df["timestamp_local"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # 숫자형 컬럼 타입을 명시해 계산 안정성을 높인다.
    for col in ["emotion_score", "intensity", "HQ_previous", "HQ_current"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values("timestamp_local").reset_index(drop=True)
    return df


def get_most_frequent_emotion(df: pd.DataFrame) -> Optional[str]:
    """최빈 감정을 반환한다. 데이터가 없으면 None."""
    if df.empty or "emotion" not in df.columns:
        return None

    mode_series = df["emotion"].mode(dropna=True)
    if mode_series.empty:
        return None

    return str(mode_series.iloc[0])


def build_hourly_hq_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """시간대(0~23시)별 평균 HQ DataFrame을 만든다."""
    if df.empty:
        return pd.DataFrame(columns=["hour", "HQ_current"])

    work = df.copy()
    work["hour"] = work["timestamp_local"].dt.hour

    hourly_df = (
        work.groupby("hour", as_index=False)["HQ_current"]
        .mean()
        .sort_values("hour")
        .reset_index(drop=True)
    )
    hourly_df["HQ_current"] = hourly_df["HQ_current"].round(2)
    return hourly_df


def build_weekday_hq_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """요일(월~일)별 평균 HQ DataFrame을 만든다."""
    if df.empty:
        return pd.DataFrame(columns=["weekday_num", "weekday_label", "HQ_current"])

    weekday_labels = {
        0: "월",
        1: "화",
        2: "수",
        3: "목",
        4: "금",
        5: "토",
        6: "일",
    }

    work = df.copy()
    work["weekday_num"] = work["timestamp_local"].dt.weekday

    weekday_df = (
        work.groupby("weekday_num", as_index=False)["HQ_current"]
        .mean()
        .sort_values("weekday_num")
        .reset_index(drop=True)
    )
    weekday_df["weekday_label"] = weekday_df["weekday_num"].map(weekday_labels)
    weekday_df["HQ_current"] = weekday_df["HQ_current"].round(2)

    return weekday_df
