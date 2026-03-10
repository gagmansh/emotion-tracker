from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from analytics import (
    PERIOD_OPTIONS,
    calculate_hourly_hq_change,
    calculate_most_common_emotion,
    calculate_weekday_hq_change,
    get_period_range,
    records_to_dataframe,
)
from firebase_utils import (
    DEFAULT_USER_ID,
    fetch_emotion_records,
    get_latest_hq,
    initialize_local_store,
    save_emotion_record,
)
from hq_logic import EMOTION_SCORES, calculate_hq


st.set_page_config(
    page_title="Emotion Tracker",
    page_icon="🙂",
    layout="wide",
)


@st.cache_resource(show_spinner=False)
def get_local_store() -> Path:
    return initialize_local_store()


def render_sidebar(storage_path: Path) -> str:
    st.sidebar.header("기본 설정")
    user_id = st.sidebar.text_input("사용자 ID", value=DEFAULT_USER_ID)
    st.sidebar.success("로컬 저장 모드")
    st.sidebar.caption(f"저장 파일: {storage_path}")
    st.sidebar.markdown(
        "`data/emotion_records.json` 파일에 기록이 저장됩니다. "
        "Firebase 설정은 필요하지 않습니다."
    )
    return user_id


def render_record_tab(storage_path: Path, user_id: str) -> None:
    st.subheader("감정 기록")
    st.caption("감정을 선택하고 강도를 입력하면 HQ를 계산한 뒤 로컬 JSON 파일에 저장합니다.")

    if not user_id.strip():
        st.warning("사이드바에 사용자 ID를 입력하세요.")
        return

    current_hq = get_latest_hq(storage_path, user_id.strip())

    emotion = st.selectbox("감정", list(EMOTION_SCORES.keys()))
    intensity = st.slider("강도", min_value=1, max_value=10, value=5, step=1)
    preview = calculate_hq(current_hq, emotion, intensity)

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("현재 HQ", f"{current_hq:.2f}")
    metric_col2.metric("감정 점수", f"{preview['emotion_score']:.2f}")
    metric_col3.metric("예상 변화량", f"{preview['delta_HQ']:+.2f}")
    metric_col4.metric("저장 후 HQ", f"{preview['HQ_current']:.2f}")

    with st.form("emotion_record_form"):
        memo = st.text_area(
            "메모 (선택)",
            placeholder="예: 회의가 잘 끝나서 기분이 좋았음",
            help="메모는 선택 항목입니다.",
        )
        submitted = st.form_submit_button("기록 저장", use_container_width=True)

    if not submitted:
        return

    try:
        saved_record = save_emotion_record(
            storage_path=storage_path,
            user_id=user_id.strip(),
            emotion=emotion,
            intensity=intensity,
            note=memo.strip(),
        )
    except Exception as exc:
        st.error("감정 기록 저장 중 오류가 발생했습니다.")
        st.exception(exc)
        return

    st.success("감정 기록을 저장했습니다.")
    saved_col1, saved_col2, saved_col3 = st.columns(3)
    saved_col1.metric("이전 HQ", f"{saved_record['HQ_previous']:.2f}")
    saved_col2.metric("현재 HQ", f"{saved_record['HQ_current']:.2f}")
    saved_col3.metric(
        "변화량",
        f"{saved_record['HQ_current'] - saved_record['HQ_previous']:+.2f}",
    )


def render_analysis_tab(storage_path: Path, user_id: str) -> None:
    st.subheader("분석 대시보드")
    st.caption("로컬에 저장된 감정 데이터를 바탕으로 주요 감정과 HQ 흐름을 확인합니다.")

    if not user_id.strip():
        st.warning("사이드바에 사용자 ID를 입력하세요.")
        return

    period = st.radio("조회 기간", PERIOD_OPTIONS, horizontal=True)
    start_at, end_at = get_period_range(period)

    try:
        records = fetch_emotion_records(
            storage_path=storage_path,
            user_id=user_id.strip(),
            start_at=start_at,
            end_at=end_at,
        )
    except Exception as exc:
        st.error("데이터를 조회하지 못했습니다.")
        st.exception(exc)
        return

    df = records_to_dataframe(records)
    if df.empty:
        st.info("선택한 기간에 저장된 감정 기록이 없습니다.")
        return

    most_common_emotion = calculate_most_common_emotion(df) or "-"
    latest_hq = float(df["HQ_current"].iloc[-1])
    average_hq = float(df["HQ_current"].mean())
    average_intensity = float(df["intensity"].mean())

    top_col1, top_col2, top_col3, top_col4 = st.columns(4)
    top_col1.metric("기록 수", f"{len(df)}개")
    top_col2.metric("최빈 감정", most_common_emotion)
    top_col3.metric("평균 HQ", f"{average_hq:.2f}")
    top_col4.metric("평균 강도", f"{average_intensity:.2f}")

    st.markdown("#### 시간 순 HQ 추이")
    history_chart = (
        df[["timestamp_local", "HQ_current"]]
        .rename(columns={"timestamp_local": "timestamp"})
        .set_index("timestamp")
    )
    st.line_chart(history_chart)
    st.caption(f"마지막 기록 기준 현재 HQ는 {latest_hq:.2f}입니다.")

    hourly_df = calculate_hourly_hq_change(df)
    weekday_df = calculate_weekday_hq_change(df)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("#### 시간대별 평균 HQ")
        if hourly_df.empty:
            st.info("시간대별로 묶을 데이터가 없습니다.")
        else:
            st.line_chart(hourly_df.set_index("hour_label")[["average_hq"]])
            st.dataframe(
                hourly_df.rename(
                    columns={
                        "hour_label": "시간대",
                        "average_hq": "평균 HQ",
                        "record_count": "기록 수",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

    with chart_col2:
        st.markdown("#### 요일별 평균 HQ")
        if weekday_df.empty:
            st.info("요일별로 묶을 데이터가 없습니다.")
        else:
            st.bar_chart(weekday_df.set_index("weekday")[["average_hq"]])
            st.dataframe(
                weekday_df.rename(
                    columns={
                        "weekday": "요일",
                        "average_hq": "평균 HQ",
                        "record_count": "기록 수",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

    st.markdown("#### 원본 기록")
    st.dataframe(format_history_table(df), use_container_width=True, hide_index=True)


def render_storage_tab(storage_path: Path, user_id: str) -> None:
    st.subheader("로컬 저장소")
    st.caption("이 앱은 인터넷이나 Firebase 없이 로컬 JSON 파일만 사용합니다.")

    st.code(str(storage_path))
    st.markdown(
        """
- 앱 데이터는 위 파일에 저장됩니다.
- 파일이 없으면 앱 시작 시 자동으로 생성됩니다.
- 다른 PC로 옮기려면 이 JSON 파일만 함께 복사하면 됩니다.
        """
    )

    if not storage_path.exists():
        st.warning("저장 파일이 아직 생성되지 않았습니다.")
        return

    raw_text = storage_path.read_text(encoding="utf-8")
    file_size = storage_path.stat().st_size
    st.metric("파일 크기", f"{file_size} bytes")

    try:
        records = fetch_emotion_records(storage_path=storage_path, user_id=user_id.strip()) if user_id.strip() else []
        st.metric("현재 사용자 기록 수", f"{len(records)}개")
    except Exception as exc:
        st.error("저장 파일을 읽는 중 오류가 발생했습니다.")
        st.exception(exc)
        return

    st.download_button(
        "JSON 파일 다운로드",
        data=raw_text,
        file_name=storage_path.name,
        mime="application/json",
        use_container_width=True,
    )


def format_history_table(df: pd.DataFrame) -> pd.DataFrame:
    table_df = df.copy()
    table_df["timestamp_local"] = table_df["timestamp_local"].dt.strftime("%Y-%m-%d %H:%M:%S")
    table_df["HQ_previous"] = table_df["HQ_previous"].round(2)
    table_df["HQ_current"] = table_df["HQ_current"].round(2)
    table_df["emotion_score"] = table_df["emotion_score"].round(2)
    table_df = table_df[
        [
            "timestamp_local",
            "emotion",
            "emotion_score",
            "intensity",
            "HQ_previous",
            "HQ_current",
            "note",
        ]
    ]
    return table_df.rename(
        columns={
            "timestamp_local": "기록 시각",
            "emotion": "감정",
            "emotion_score": "감정 점수",
            "intensity": "강도",
            "HQ_previous": "이전 HQ",
            "HQ_current": "현재 HQ",
            "note": "메모",
        }
    )


def main() -> None:
    st.title("Emotion Tracker")
    st.caption("감정 기록과 HQ 분석을 위한 로컬 전용 Streamlit 앱")

    try:
        storage_path = get_local_store()
    except Exception as exc:
        st.error("로컬 저장소 초기화에 실패했습니다.")
        st.exception(exc)
        st.stop()

    user_id = render_sidebar(storage_path)
    record_tab, analysis_tab, storage_tab = st.tabs(
        ["감정 기록", "분석 대시보드", "로컬 저장소"]
    )

    with record_tab:
        render_record_tab(storage_path, user_id)

    with analysis_tab:
        render_analysis_tab(storage_path, user_id)

    with storage_tab:
        render_storage_tab(storage_path, user_id)


if __name__ == "__main__":
    main()
