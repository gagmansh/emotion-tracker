from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Sequence

import pandas as pd


PERIOD_OPTIONS = ("오늘", "이번 주", "이번 달", "전체")

WEEKDAY_LABELS = {
    0: "월",
    1: "화",
    2: "수",
    3: "목",
    4: "금",
    5: "토",
    6: "일",
}


def get_period_range(period: str, now: datetime | None = None) -> tuple[datetime | None, datetime | None]:
    local_now = now.astimezone() if now else datetime.now().astimezone()
    end_at = local_now.astimezone(timezone.utc)
    start_of_day = local_now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "오늘":
        start_at = start_of_day
    elif period == "이번 주":
        start_at = start_of_day - timedelta(days=start_of_day.weekday())
    elif period == "이번 달":
        start_at = start_of_day.replace(day=1)
    elif period == "전체":
        return None, None
    else:
        raise ValueError(f"지원하지 않는 조회 기간입니다: {period}")

    return start_at.astimezone(timezone.utc), end_at


def records_to_dataframe(records: Sequence[dict]) -> pd.DataFrame:
    columns = [
        "id",
        "timestamp",
        "timestamp_local",
        "emotion",
        "emotion_score",
        "intensity",
        "HQ_previous",
        "HQ_current",
        "note",
    ]
    if not records:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(list(records)).copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    local_tz = datetime.now().astimezone().tzinfo
    df["timestamp_local"] = df["timestamp"].dt.tz_convert(local_tz)

    for column_name in ["emotion_score", "intensity", "HQ_previous", "HQ_current"]:
        if column_name in df.columns:
            df[column_name] = pd.to_numeric(df[column_name], errors="coerce")

    if "note" not in df.columns:
        df["note"] = ""

    df["hour"] = df["timestamp_local"].dt.hour
    df["hour_label"] = df["hour"].map(lambda hour: f"{int(hour):02d}:00")
    df["weekday_num"] = df["timestamp_local"].dt.weekday
    df["weekday"] = df["weekday_num"].map(WEEKDAY_LABELS)

    return df.sort_values("timestamp_local").reset_index(drop=True)


def calculate_most_common_emotion(df: pd.DataFrame) -> str | None:
    if df.empty or "emotion" not in df.columns:
        return None

    mode_series = df["emotion"].mode(dropna=True)
    if mode_series.empty:
        return None
    return str(mode_series.iloc[0])


def calculate_hourly_hq_change(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["hour", "hour_label", "average_hq", "record_count"])

    hourly_df = (
        df.groupby(["hour", "hour_label"], as_index=False)
        .agg(
            average_hq=("HQ_current", "mean"),
            record_count=("HQ_current", "size"),
        )
        .sort_values("hour")
        .reset_index(drop=True)
    )
    hourly_df["average_hq"] = hourly_df["average_hq"].round(2)
    return hourly_df


def calculate_weekday_hq_change(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["weekday_num", "weekday", "average_hq", "record_count"])

    weekday_df = (
        df.groupby(["weekday_num", "weekday"], as_index=False)
        .agg(
            average_hq=("HQ_current", "mean"),
            record_count=("HQ_current", "size"),
        )
        .sort_values("weekday_num")
        .reset_index(drop=True)
    )
    weekday_df["average_hq"] = weekday_df["average_hq"].round(2)
    return weekday_df
