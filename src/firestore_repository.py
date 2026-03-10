from datetime import datetime, timezone
from typing import Dict, List

from src.hq_calculator import calculate_hq


class EmotionRecordRepository:
    """emotion_records 컬렉션 접근 전용 저장소 클래스."""

    def __init__(self, db, collection_name: str = "emotion_records"):
        self.collection = db.collection(collection_name)

    @staticmethod
    def _normalize_timestamp(ts):
        """
        Firestore timestamp를 timezone-aware datetime으로 표준화한다.
        naive datetime이면 UTC로 간주한다.
        """
        if not isinstance(ts, datetime):
            return None
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts

    def get_latest_hq(self, user_id: str) -> float:
        """
        특정 user_id의 최신 HQ를 가져온다.
        기록이 없으면 기본 시작값 50을 반환한다.
        """
        docs = self.collection.where("user_id", "==", user_id).stream()

        latest_ts = None
        latest_hq = 50.0

        for doc in docs:
            data = doc.to_dict()
            ts = self._normalize_timestamp(data.get("timestamp"))
            if ts is None:
                continue

            if latest_ts is None or ts > latest_ts:
                latest_ts = ts
                latest_hq = float(data.get("HQ_current", 50.0))

        return round(latest_hq, 2)

    def save_emotion_record(self, user_id: str, emotion: str, intensity: int) -> Dict:
        """
        감정 기록을 저장한다.
        저장 시점에서 HQ_previous/HQ_current를 자동 계산해 함께 저장한다.
        """
        hq_previous = self.get_latest_hq(user_id)
        calc = calculate_hq(hq_previous=hq_previous, emotion=emotion, intensity=intensity)

        # Firestore 정렬/비교를 위해 UTC timezone-aware datetime 사용
        record = {
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc),
            "emotion": emotion,
            "emotion_score": calc["emotion_score"],
            "intensity": int(intensity),
            "HQ_previous": calc["HQ_previous"],
            "HQ_current": calc["HQ_current"],
        }

        doc_ref = self.collection.document()
        doc_ref.set(record)

        record["id"] = doc_ref.id
        return record

    def get_records_in_range(
        self, user_id: str, start_utc: datetime, end_utc: datetime
    ) -> List[Dict]:
        """
        기간 필터 조건으로 감정 기록을 가져온다.
        - user_id 동일
        - start_utc <= timestamp <= end_utc
        """
        query = self.collection.where("user_id", "==", user_id)

        rows: List[Dict] = []
        for doc in query.stream():
            data = doc.to_dict()
            ts = self._normalize_timestamp(data.get("timestamp"))
            if ts is None:
                continue

            # 기간 범위 조건을 파이썬에서 명시적으로 필터링한다.
            if not (start_utc <= ts <= end_utc):
                continue

            data["id"] = doc.id
            data["timestamp"] = ts
            rows.append(data)

        rows.sort(key=lambda x: x["timestamp"])
        return rows
