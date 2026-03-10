from __future__ import annotations

import pandas as pd
import streamlit as st

from firebase_utils import DEFAULT_USER_ID
from frontend.api_client import (
    DEFAULT_API_BASE_URL,
    ApiClientError,
    EmotionTrackerApiClient,
)
from hq_logic import EMOTION_SCORES, calculate_hq


PERIOD_OPTIONS = {
    "오늘": "today",
    "이번 주": "week",
    "이번 달": "month",
    "전체": "all",
}


def render_sidebar() -> tuple[EmotionTrackerApiClient, str, dict | None, dict | None, str | None]:
    st.sidebar.header("서비스 모드 설정")
    backend_url = st.sidebar.text_input("Backend URL", value=DEFAULT_API_BASE_URL)
    user_id = st.sidebar.text_input("사용자 ID", value=DEFAULT_USER_ID)

    client = EmotionTrackerApiClient(base_url=backend_url)

    health_payload = None
    storage_payload = None
    api_error = None

    try:
        health_payload = client.health()
        storage_payload = client.storage_info()
        st.sidebar.success("백엔드 연결 완료")
        st.sidebar.caption(
            f"Storage Backend: {storage_payload.get('backend', health_payload.get('storage_backend', '-'))}"
        )
    except ApiClientError as exc:
        api_error = str(exc)
        st.sidebar.error("백엔드 연결 실패")

    return client, user_id, health_payload, storage_payload, api_error


def render_record_tab(client: EmotionTrackerApiClient, user_id: str, api_error: str | None) -> None:
    st.subheader("감정 기록")
    st.caption("Streamlit 프론트엔드가 FastAPI 백엔드에 감정 기록을 저장합니다.")

    if api_error is not None:
        st.error(api_error)
        st.info("먼저 `run_backend.bat` 또는 `python -m uvicorn backend.app.main:app --reload`로 API를 실행하세요.")
        return

    if not user_id.strip():
        st.warning("사이드바에 사용자 ID를 입력하세요.")
        return

    try:
        current_hq_payload = client.get_current_hq(user_id.strip())
        current_hq = float(current_hq_payload["current_hq"])
    except ApiClientError as exc:
        st.error(str(exc))
        return

    emotion = st.selectbox("감정", list(EMOTION_SCORES.keys()))
    intensity = st.slider("강도", min_value=1, max_value=10, value=5, step=1)
    preview = calculate_hq(current_hq, emotion, intensity)

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("현재 HQ", f"{current_hq:.2f}")
    metric_col2.metric("감정 점수", f"{preview['emotion_score']:.2f}")
    metric_col3.metric("예상 변화량", f"{preview['delta_HQ']:+.2f}")
    metric_col4.metric("저장 후 HQ", f"{preview['HQ_current']:.2f}")

    with st.form("service_record_form"):
        note = st.text_area("메모 (선택)", placeholder="예: 발표가 잘 끝나서 안도감이 들었음")
        submitted = st.form_submit_button("백엔드에 저장", use_container_width=True)

    if not submitted:
        return

    try:
        saved_record = client.create_record(
            user_id=user_id.strip(),
            emotion=emotion,
            intensity=intensity,
            note=note.strip(),
        )
    except ApiClientError as exc:
        st.error(str(exc))
        return

    st.success("감정 기록을 저장했습니다.")
    saved_col1, saved_col2, saved_col3 = st.columns(3)
    saved_col1.metric("이전 HQ", f"{saved_record['HQ_previous']:.2f}")
    saved_col2.metric("현재 HQ", f"{saved_record['HQ_current']:.2f}")
    saved_col3.metric(
        "변화량",
        f"{saved_record['HQ_current'] - saved_record['HQ_previous']:+.2f}",
    )


def render_analysis_tab(client: EmotionTrackerApiClient, user_id: str, api_error: str | None) -> None:
    st.subheader("분석 대시보드")
    st.caption("분석 데이터도 백엔드에서 계산해 전달합니다.")

    if api_error is not None:
        st.error(api_error)
        return

    if not user_id.strip():
        st.warning("사이드바에 사용자 ID를 입력하세요.")
        return

    selected_period_label = st.radio("조회 기간", list(PERIOD_OPTIONS.keys()), horizontal=True)
    period = PERIOD_OPTIONS[selected_period_label]

    try:
        payload = client.get_analytics(user_id=user_id.strip(), period=period)
    except ApiClientError as exc:
        st.error(str(exc))
        return

    summary = payload["summary"]
    records = payload["records"]

    if not records:
        st.info("선택한 기간에 저장된 기록이 없습니다.")
        return

    top_col1, top_col2, top_col3, top_col4 = st.columns(4)
    top_col1.metric("기록 수", f"{summary['record_count']}개")
    top_col2.metric("최빈 감정", summary["most_common_emotion"] or "-")
    top_col3.metric("평균 HQ", f"{summary['average_hq']:.2f}")
    top_col4.metric("평균 강도", f"{summary['average_intensity']:.2f}")

    records_df = pd.DataFrame(records)
    records_df["timestamp"] = pd.to_datetime(records_df["timestamp"], utc=True, errors="coerce")
    records_df["timestamp_local"] = records_df["timestamp"].dt.tz_convert(None)

    st.markdown("#### 시간 순 HQ 추이")
    history_chart = (
        records_df[["timestamp_local", "HQ_current"]]
        .rename(columns={"timestamp_local": "timestamp"})
        .set_index("timestamp")
    )
    st.line_chart(history_chart)
    st.caption(f"마지막 기록 기준 현재 HQ는 {summary['current_hq']:.2f}입니다.")

    hourly_df = pd.DataFrame(payload["hourly"])
    weekday_df = pd.DataFrame(payload["weekday"])

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("#### 시간대별 평균 HQ")
        if hourly_df.empty:
            st.info("시간대별 데이터가 없습니다.")
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
            st.info("요일별 데이터가 없습니다.")
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
    records_df["timestamp_local"] = records_df["timestamp_local"].dt.strftime("%Y-%m-%d %H:%M:%S")
    table_df = records_df[
        [
            "timestamp_local",
            "emotion",
            "emotion_score",
            "intensity",
            "HQ_previous",
            "HQ_current",
            "note",
        ]
    ].rename(
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
    st.dataframe(table_df, use_container_width=True, hide_index=True)


def render_system_tab(
    health_payload: dict | None,
    storage_payload: dict | None,
    api_error: str | None,
) -> None:
    st.subheader("서비스 구조")
    st.markdown(
        """
- 프론트엔드: Streamlit
- 백엔드: FastAPI
- 현재 저장소: JSON 또는 Firestore
- 향후 배포: Cloudflare는 프록시/도메인/보안 계층으로 붙이면 됩니다.
        """
    )

    if api_error is not None:
        st.error(api_error)
    else:
        st.success("백엔드가 정상 연결되어 있습니다.")
        st.json(
            {
                "health": health_payload,
                "storage": storage_payload,
            }
        )

    st.markdown(
        """
실행 순서:

1. `run_backend.bat`
2. `run_frontend.bat`

또는 한 번에:

`run_stack.bat`
        """
    )


def main() -> None:
    st.set_page_config(
        page_title="Emotion Tracker Service Frontend",
        page_icon="🌐",
        layout="wide",
    )
    st.title("Emotion Tracker Service Frontend")
    st.caption("외부 서비스형 구조를 위한 Streamlit 프론트엔드")

    client, user_id, health_payload, storage_payload, api_error = render_sidebar()
    record_tab, analysis_tab, system_tab = st.tabs(
        ["감정 기록", "분석 대시보드", "서비스 상태"]
    )

    with record_tab:
        render_record_tab(client, user_id, api_error)

    with analysis_tab:
        render_analysis_tab(client, user_id, api_error)

    with system_tab:
        render_system_tab(health_payload, storage_payload, api_error)


if __name__ == "__main__":
    main()
