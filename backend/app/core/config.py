from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def load_dotenv_file(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    storage_backend: str
    local_data_path: str
    default_user_id: str
    firestore_collection_name: str
    firebase_service_account_path: str
    firebase_service_account_json: str
    frontend_api_base_url: str
    cors_origins: tuple[str, ...]


def _parse_cors_origins(raw_value: str) -> tuple[str, ...]:
    if not raw_value.strip():
        return (
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            "http://localhost:8501",
            "http://127.0.0.1:8501",
            "http://localhost:8502",
            "http://127.0.0.1:8502",
        )

    return tuple(
        origin.strip()
        for origin in raw_value.split(",")
        if origin.strip()
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv_file()

    return Settings(
        storage_backend=os.getenv("APP_STORAGE_BACKEND", "json").strip().lower() or "json",
        local_data_path=os.getenv("LOCAL_DATA_PATH", "./data/emotion_records.json").strip()
        or "./data/emotion_records.json",
        default_user_id=os.getenv("DEFAULT_USER_ID", "demo_user").strip() or "demo_user",
        firestore_collection_name=os.getenv("FIRESTORE_COLLECTION_NAME", "emotion_records").strip()
        or "emotion_records",
        firebase_service_account_path=os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip(),
        firebase_service_account_json=os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip(),
        frontend_api_base_url=os.getenv("FRONTEND_API_BASE_URL", "http://127.0.0.1:8000").strip()
        or "http://127.0.0.1:8000",
        cors_origins=_parse_cors_origins(os.getenv("APP_CORS_ORIGINS", "")),
    )
