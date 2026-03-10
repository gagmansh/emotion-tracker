from functools import lru_cache
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore

from src.config import get_config


def _credential_from_streamlit_secrets() -> Optional[object]:
    """
    Streamlit secrets 기반 자격 증명 로딩.
    - .streamlit/secrets.toml 에 [firebase_service_account] 블록이 있는 경우 사용한다.
    """
    try:
        import streamlit as st
    except Exception:
        return None

    if "firebase_service_account" not in st.secrets:
        return None

    service_account_info = dict(st.secrets["firebase_service_account"])

    # private_key 줄바꿈 이스케이프 처리를 복구한다.
    if "private_key" in service_account_info:
        service_account_info["private_key"] = service_account_info["private_key"].replace(
            "\\n", "\n"
        )

    return credentials.Certificate(service_account_info)


@lru_cache(maxsize=1)
def get_firestore_client():
    """
    Firebase Admin 앱/클라이언트를 단일 인스턴스로 초기화한다.
    우선순위:
    1) .env 의 FIREBASE_SERVICE_ACCOUNT_PATH
    2) Streamlit secrets 의 firebase_service_account
    """
    config = get_config()

    if not firebase_admin._apps:
        if config.firebase_service_account_path:
            cred = credentials.Certificate(config.firebase_service_account_path)
            firebase_admin.initialize_app(cred)
        else:
            secret_cred = _credential_from_streamlit_secrets()
            if secret_cred is None:
                raise ValueError(
                    "Firebase 자격 증명이 없습니다. "
                    "FIREBASE_SERVICE_ACCOUNT_PATH(.env) 또는 "
                    ".streamlit/secrets.toml을 설정해 주세요."
                )
            firebase_admin.initialize_app(secret_cred)

    return firestore.client()
