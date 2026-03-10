import matplotlib.pyplot as plt
from matplotlib import font_manager


def setup_korean_font() -> None:
    """
    matplotlib 한글 깨짐 방지 설정.
    Windows(맑은 고딕) 우선으로 탐색하고, 없으면 대체 폰트를 시도한다.
    """
    preferred_fonts = [
        "Malgun Gothic",  # Windows
        "NanumGothic",
        "AppleGothic",  # macOS
        "Noto Sans CJK KR",
    ]

    installed_fonts = {font.name for font in font_manager.fontManager.ttflist}
    selected_font = None

    for font_name in preferred_fonts:
        if font_name in installed_fonts:
            selected_font = font_name
            break

    if selected_font:
        plt.rcParams["font.family"] = selected_font

    # 마이너스 기호 깨짐 방지
    plt.rcParams["axes.unicode_minus"] = False


def plot_hourly_hq(hourly_df):
    """시간대별 평균 HQ 라인 그래프를 생성한다."""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_title("시간대별 HQ 변화")

    if hourly_df.empty:
        ax.text(0.5, 0.5, "표시할 데이터가 없습니다.", ha="center", va="center")
        ax.set_axis_off()
        return fig

    ax.plot(hourly_df["hour"], hourly_df["HQ_current"], marker="o", color="#2E8B57")
    ax.set_xlabel("시간(시)")
    ax.set_ylabel("평균 HQ")
    ax.set_xticks(range(0, 24, 2))
    ax.set_ylim(0, 100)
    ax.grid(alpha=0.3)

    return fig


def plot_weekday_hq(weekday_df):
    """요일별 평균 HQ 막대 그래프를 생성한다."""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_title("요일별 HQ 변화")

    if weekday_df.empty:
        ax.text(0.5, 0.5, "표시할 데이터가 없습니다.", ha="center", va="center")
        ax.set_axis_off()
        return fig

    ax.bar(weekday_df["weekday_label"], weekday_df["HQ_current"], color="#4C78A8")
    ax.set_xlabel("요일")
    ax.set_ylabel("평균 HQ")
    ax.set_ylim(0, 100)
    ax.grid(axis="y", alpha=0.3)

    return fig
