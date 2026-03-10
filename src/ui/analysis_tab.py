import streamlit as st

from src.analysis_service import (
    PERIOD_OPTIONS,
    build_hourly_hq_dataframe,
    build_weekday_hq_dataframe,
    get_most_frequent_emotion,
    get_period_range_utc,
    records_to_dataframe,
)
from src.plot_utils import plot_hourly_hq, plot_weekday_hq, setup_korean_font


def render_analysis_tab(repository, user_id: str) -> None:
    """탭 2: 감정 분석 UI 렌더링."""
    st.subheader("감정 분석")
    st.caption("날짜 필터로 기록을 조회하고 HQ 변화를 확인합니다.")

    period = st.selectbox("조회 기간", PERIOD_OPTIONS, index=0)

    if not user_id.strip():
        st.warning("사이드바에서 user_id를 입력하면 분석 데이터를 확인할 수 있습니다.")
        return

    start_utc, end_utc = get_period_range_utc(period)

    try:
        records = repository.get_records_in_range(
            user_id=user_id.strip(),
            start_utc=start_utc,
            end_utc=end_utc,
        )
    except Exception as exc:
        st.error(f"데이터 조회 중 오류가 발생했습니다: {exc}")
        return

    df = records_to_dataframe(records)
    if df.empty:
        st.info("선택한 기간에 감정 기록이 없습니다.")
        return

    most_frequent = get_most_frequent_emotion(df)
    st.metric("가장 자주 기록한 감정", most_frequent if most_frequent else "-")

    # 분석용 원본 데이터 테이블
    table_df = df[
        ["timestamp_str", "emotion", "emotion_score", "intensity", "HQ_previous", "HQ_current"]
    ].copy()
    table_df = table_df.rename(
        columns={
            "timestamp_str": "기록 시각",
            "emotion": "감정",
            "emotion_score": "감정 점수",
            "intensity": "강도",
            "HQ_previous": "이전 HQ",
            "HQ_current": "현재 HQ",
        }
    )
    st.dataframe(table_df, use_container_width=True, hide_index=True)

    setup_korean_font()

    hourly_df = build_hourly_hq_dataframe(df)
    weekday_df = build_weekday_hq_dataframe(df)

    st.markdown("### 시간대별 HQ 변화 그래프")
    st.pyplot(plot_hourly_hq(hourly_df), use_container_width=True)

    st.markdown("### 요일별 HQ 변화 그래프")
    st.pyplot(plot_weekday_hq(weekday_df), use_container_width=True)
