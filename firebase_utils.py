from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from hq_logic import calculate_hq


def _load_dotenv_file(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv_file()

DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "demo_user").strip() or "demo_user"
DEFAULT_STORAGE_PATH = os.getenv("LOCAL_DATA_PATH", "./data/emotion_records.json").strip()


def get_storage_path(raw_path: str | None = None) -> Path:
    candidate = (raw_path or DEFAULT_STORAGE_PATH or "./data/emotion_records.json").strip()
    path = Path(candidate)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def initialize_local_store(storage_path: str | Path | None = None) -> Path:
    path = get_storage_path(str(storage_path) if storage_path is not None else None)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        path.write_text("[]", encoding="utf-8")

    return path


def _normalize_datetime(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    raise TypeError(f"지원하지 않는 timestamp 타입입니다: {type(value)}")


def _read_all_records(storage_path: str | Path | None = None) -> list[dict[str, Any]]:
    path = initialize_local_store(storage_path)

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"로컬 데이터 파일이 손상되었습니다: {path}") from exc

    if not isinstance(payload, list):
        raise RuntimeError(f"로컬 데이터 파일 형식이 올바르지 않습니다: {path}")

    return payload


def _write_all_records(records: list[dict[str, Any]], storage_path: str | Path | None = None) -> Path:
    path = initialize_local_store(storage_path)
    path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def get_latest_hq(storage_path: str | Path, user_id: str) -> float:
    latest_timestamp: datetime | None = None
    latest_hq = 50.0

    for record in _read_all_records(storage_path):
        if record.get("user_id") != user_id:
            continue

        timestamp = _normalize_datetime(record.get("timestamp"))
        if timestamp is None:
            continue

        if latest_timestamp is None or timestamp > latest_timestamp:
            latest_timestamp = timestamp
            latest_hq = float(record.get("HQ_current", 50.0))

    return round(latest_hq, 2)


def save_emotion_record(
    storage_path: str | Path,
    user_id: str,
    emotion: str,
    intensity: int,
    note: str = "",
    recorded_at: datetime | None = None,
) -> dict[str, Any]:
    if not user_id.strip():
        raise ValueError("user_id는 비워둘 수 없습니다.")

    normalized_user_id = user_id.strip()
    record_time = _normalize_datetime(recorded_at) or datetime.now(timezone.utc)
    hq_previous = get_latest_hq(storage_path, normalized_user_id)
    hq_result = calculate_hq(hq_previous=hq_previous, emotion=emotion, intensity=intensity)

    record = {
        "id": uuid4().hex,
        "user_id": normalized_user_id,
        "timestamp": record_time.isoformat(),
        "emotion": emotion,
        "emotion_score": hq_result["emotion_score"],
        "intensity": int(intensity),
        "HQ_previous": hq_result["HQ_previous"],
        "HQ_current": hq_result["HQ_current"],
        "note": note,
    }

    records = _read_all_records(storage_path)
    records.append(record)
    _write_all_records(records, storage_path)

    saved_record = dict(record)
    saved_record["timestamp"] = record_time
    return saved_record


def fetch_emotion_records(
    storage_path: str | Path,
    user_id: str,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> list[dict[str, Any]]:
    normalized_start = _normalize_datetime(start_at)
    normalized_end = _normalize_datetime(end_at)

    records: list[dict[str, Any]] = []
    for record in _read_all_records(storage_path):
        if record.get("user_id") != user_id:
            continue

        timestamp = _normalize_datetime(record.get("timestamp"))
        if timestamp is None:
            continue

        if normalized_start is not None and timestamp < normalized_start:
            continue
        if normalized_end is not None and timestamp > normalized_end:
            continue

        normalized_record = dict(record)
        normalized_record["timestamp"] = timestamp
        normalized_record.setdefault("note", "")
        records.append(normalized_record)

    records.sort(key=lambda item: item["timestamp"])
    return records
