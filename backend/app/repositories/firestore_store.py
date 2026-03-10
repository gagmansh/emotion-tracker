from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from hq_logic import calculate_hq


class FirestoreEmotionRepository:
    def __init__(
        self,
        service_account_path: str,
        service_account_json: str,
        collection_name: str,
    ):
        if not service_account_path.strip() and not service_account_json.strip():
            raise RuntimeError(
                "Firestore 백엔드를 쓰려면 "
                "`FIREBASE_SERVICE_ACCOUNT_PATH` 또는 "
                "`FIREBASE_SERVICE_ACCOUNT_JSON`이 필요합니다."
            )

        self.service_account_path = (
            self._resolve_path(service_account_path) if service_account_path.strip() else ""
        )
        self.service_account_json = service_account_json
        self.collection_name = collection_name
        self.db = self._get_client(self.service_account_path, self.service_account_json)
        self.collection = self.db.collection(collection_name)

    @staticmethod
    def _resolve_path(raw_path: str) -> str:
        path = Path(raw_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        return str(path.resolve())

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_client(service_account_path: str, service_account_json: str):
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
        except ImportError as exc:
            raise RuntimeError(
                "Firestore 백엔드를 사용하려면 `pip install -r requirements-firestore.txt`가 필요합니다."
            ) from exc

        if not firebase_admin._apps:
            if service_account_json.strip():
                try:
                    service_account_info = json.loads(service_account_json)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        "FIREBASE_SERVICE_ACCOUNT_JSON이 올바른 JSON 형식이 아닙니다."
                    ) from exc

                firebase_admin.initialize_app(
                    credentials.Certificate(service_account_info)
                )
            else:
                credential_path = Path(service_account_path)
                if not credential_path.exists():
                    raise FileNotFoundError(
                        f"Firebase 서비스 계정 파일을 찾을 수 없습니다: {credential_path}"
                    )

                firebase_admin.initialize_app(
                    credentials.Certificate(str(credential_path))
                )

        return firestore.client()

    @staticmethod
    def _user_query(collection, user_id: str):
        from google.cloud.firestore_v1.base_query import FieldFilter

        return collection.where(filter=FieldFilter("user_id", "==", user_id))

    @staticmethod
    def _normalize_timestamp(value: Any) -> datetime | None:
        if not isinstance(value, datetime):
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def get_latest_hq(self, user_id: str) -> float:
        latest_timestamp: datetime | None = None
        latest_hq = 50.0

        for document in self._user_query(self.collection, user_id).stream():
            payload = document.to_dict()
            timestamp = self._normalize_timestamp(payload.get("timestamp"))
            if timestamp is None:
                continue

            if latest_timestamp is None or timestamp > latest_timestamp:
                latest_timestamp = timestamp
                latest_hq = float(payload.get("HQ_current", 50.0))

        return round(latest_hq, 2)

    def save_record(
        self,
        user_id: str,
        emotion: str,
        intensity: int,
        note: str = "",
        recorded_at: datetime | None = None,
    ) -> dict[str, Any]:
        normalized_user_id = user_id.strip()
        if not normalized_user_id:
            raise ValueError("user_id는 비워둘 수 없습니다.")

        record_time = recorded_at or datetime.now(timezone.utc)
        previous_hq = self.get_latest_hq(normalized_user_id)
        hq_result = calculate_hq(previous_hq, emotion, intensity)

        record = {
            "user_id": normalized_user_id,
            "timestamp": record_time,
            "emotion": emotion,
            "emotion_score": hq_result["emotion_score"],
            "intensity": int(intensity),
            "HQ_previous": hq_result["HQ_previous"],
            "HQ_current": hq_result["HQ_current"],
            "note": note,
        }

        document = self.collection.document()
        document.set(record)

        saved_record = dict(record)
        saved_record["id"] = document.id
        return saved_record

    def list_records(
        self,
        user_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []

        for document in self._user_query(self.collection, user_id).stream():
            payload = document.to_dict()
            timestamp = self._normalize_timestamp(payload.get("timestamp"))
            if timestamp is None:
                continue

            if start_at is not None and timestamp < start_at.astimezone(timezone.utc):
                continue
            if end_at is not None and timestamp > end_at.astimezone(timezone.utc):
                continue

            payload["id"] = document.id
            payload["timestamp"] = timestamp
            payload.setdefault("note", "")
            records.append(payload)

        records.sort(key=lambda item: item["timestamp"])
        return records

    def get_storage_info(self) -> dict[str, Any]:
        return {
            "backend": "firestore",
            "firestore_collection": self.collection_name,
            "service_account_path": self.service_account_path or None,
        }
