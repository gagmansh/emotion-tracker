import streamlit as st

from src.hq_calculator import EMOTION_SCORES


def render_record_tab(repository, user_id: str) -> None:
    """탭 1: 감정 기록 UI 렌더링."""
    st.subheader("감정 기록")
    st.caption("감정을 선택하고 강도(1~10)를 입력하면 HQ가 자동 계산됩니다.")

    emotion_options = list(EMOTION_SCORES.keys())

    col1, col2 = st.columns([2, 1])
    with col1:
        emotion = st.selectbox(
            "감정 선택",
            emotion_options,
            index=0,
            help="이모지 + 감정 이름으로 선택합니다.",
        )
    with col2:
        intensity = st.slider("강도", min_value=1, max_value=10, value=5, step=1)

    st.write(f"현재 선택 감정 점수: **{EMOTION_SCORES[emotion]}**")

    if st.button("기록하기", type="primary", use_container_width=True):
        if not user_id.strip():
            st.error("user_id가 비어 있습니다. 사이드바에서 user_id를 입력해 주세요.")
            return

        try:
            saved = repository.save_emotion_record(
                user_id=user_id.strip(),
                emotion=emotion,
                intensity=intensity,
            )
        except Exception as exc:
            st.error(f"기록 저장 중 오류가 발생했습니다: {exc}")
            return

        st.success("감정 기록이 저장되었습니다.")

        prev_col, curr_col = st.columns(2)
        prev_col.metric("이전 HQ", saved["HQ_previous"])
        curr_col.metric(
            "현재 HQ",
            saved["HQ_current"],
            delta=round(saved["HQ_current"] - saved["HQ_previous"], 2),
        )
