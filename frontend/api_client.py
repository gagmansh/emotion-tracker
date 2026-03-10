from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests


def _load_dotenv_file(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv_file()

DEFAULT_API_BASE_URL = (
    os.getenv("FRONTEND_API_BASE_URL", "http://127.0.0.1:8000").strip()
    or "http://127.0.0.1:8000"
)


class ApiClientError(RuntimeError):
    pass


class EmotionTrackerApiClient:
    def __init__(self, base_url: str | None = None, timeout: float = 10.0):
        self.base_url = (base_url or DEFAULT_API_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def storage_info(self) -> dict[str, Any]:
        return self._request("GET", "/storage")

    def get_current_hq(self, user_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/users/{user_id}/hq")

    def create_record(
        self,
        user_id: str,
        emotion: str,
        intensity: int,
        note: str = "",
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/users/{user_id}/records",
            json={
                "emotion": emotion,
                "intensity": intensity,
                "note": note,
            },
        )

    def list_records(self, user_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/v1/users/{user_id}/records")

    def get_analytics(self, user_id: str, period: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/api/v1/users/{user_id}/analytics",
            params={"period": period},
        )

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Any:
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ApiClientError(
                f"백엔드 호출에 실패했습니다: {method} {url} ({exc})"
            ) from exc

        try:
            return response.json()
        except ValueError as exc:
            raise ApiClientError(f"백엔드 응답이 JSON이 아닙니다: {url}") from exc
