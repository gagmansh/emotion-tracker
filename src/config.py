import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# .env 파일을 자동 로드한다.
load_dotenv()

# Firestore 컬렉션명은 프로젝트 규칙에 따라 고정한다.
FIRESTORE_COLLECTION_NAME = "emotion_records"


@dataclass(frozen=True)
class AppConfig:
    """앱에서 공통으로 쓰는 설정 값 묶음."""

    firebase_service_account_path: str
    default_user_id: str


def _resolve_path(raw_path: str) -> str:
    """상대 경로 입력도 안전하게 절대 경로로 변환한다."""
    if not raw_path:
        return ""

    path = Path(raw_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    return str(path.resolve())


def get_config() -> AppConfig:
    """환경 변수(.env 포함) 기반 설정 객체를 반환한다."""
    return AppConfig(
        firebase_service_account_path=_resolve_path(
            os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")
        ),
        default_user_id=os.getenv("DEFAULT_USER_ID", "demo_user"),
    )
