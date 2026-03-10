# Emotion Tracker

감정 기록과 HQ(Happiness Quotient) 분석을 위한 웹 프로젝트입니다.

이 저장소는 이제 다음 구조를 기준으로 사용합니다.

- 프론트엔드: HTML + CSS + JavaScript 정적 웹앱
- 백엔드: FastAPI
- 저장소: Firebase Firestore
- 배포 방향:
  - 프론트엔드: Cloudflare Pages
  - 백엔드 API: 별도 Python 호스팅(Render, Railway, Fly.io, Google Cloud Run 등)
  - 도메인/프록시: Cloudflare

## 1. 구조

```text
emotion_tracker/
├─ backend/
│  └─ app/
│     ├─ main.py
│     ├─ api/routes/
│     ├─ services/
│     ├─ repositories/
│     ├─ schemas/
│     └─ core/
├─ web/
│  ├─ index.html
│  ├─ styles.css
│  ├─ app.js
│  ├─ config.js
│  └─ config.example.js
├─ hq_logic.py
├─ analytics.py
├─ run_backend.bat
├─ run_frontend.bat
├─ run_stack.bat
├─ requirements.txt
├─ .env.example
└─ secrets/
   └─ firebase_service_account.json
```

## 2. 현재 동작 방식

### 로컬 개발

- 백엔드: `http://127.0.0.1:8000`
- 정적 웹 프론트: `http://127.0.0.1:5500`
- 백엔드가 정적 사이트를 직접 서빙할 때: `http://127.0.0.1:8000/app/`

### 실제 서비스 배포

권장 구조:

```text
사용자
  -> https://app.example.com      (Cloudflare Pages)
  -> https://api.example.com      (FastAPI 백엔드 + Cloudflare 프록시)
  -> Firestore
```

즉, Cloudflare는 도메인/HTTPS/프록시 계층이고, Python 백엔드 자체는 별도 호스팅이 필요합니다.

## 3. 먼저 설치할 것

### 3-1. 가상환경 생성

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3-2. 패키지 설치

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Firebase Firestore 준비

이 프로젝트를 Firestore로 실제 연결하려면 Firebase 프로젝트와 서비스 계정 JSON이 필요합니다.

### 4-1. Firebase 프로젝트 생성

1. Firebase Console로 이동합니다.
2. 새 프로젝트를 만듭니다.
3. 왼쪽 메뉴에서 `Firestore Database`를 활성화합니다.

공식 문서:

- Firebase Admin SDK setup:
  https://firebase.google.com/docs/admin/setup
- Firestore:
  https://firebase.google.com/docs/firestore

### 4-2. 서비스 계정 JSON 다운로드

1. Firebase Console에서 `프로젝트 설정`
2. `서비스 계정`
3. `새 비공개 키 생성`
4. JSON 파일 다운로드

### 4-3. JSON 파일 저장

프로젝트 루트에 아래처럼 넣습니다.

```text
emotion_tracker/
└─ secrets/
   └─ firebase_service_account.json
```

## 5. `.env` 설정

`.env.example`를 복사해서 `.env`를 만듭니다.

예시:

```env
DEFAULT_USER_ID=demo_user
LOCAL_DATA_PATH=./data/emotion_records.json
FRONTEND_API_BASE_URL=http://127.0.0.1:8000
APP_STORAGE_BACKEND=firestore
FIREBASE_SERVICE_ACCOUNT_PATH=./secrets/firebase_service_account.json
FIRESTORE_COLLECTION_NAME=emotion_records
APP_CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500,http://localhost:8502,http://127.0.0.1:8502,https://app.example.com
```

중요 항목:

- `APP_STORAGE_BACKEND=firestore`
  Firestore 사용 활성화
- `FIREBASE_SERVICE_ACCOUNT_PATH`
  서비스 계정 JSON 경로
- `APP_CORS_ORIGINS`
  웹 프론트가 접근할 도메인 목록

## 6. 로컬 실행 방법

### 방법 A. 백엔드만 실행

```powershell
.\run_backend.bat
```

이 경우:

- API: `http://127.0.0.1:8000`
- 웹앱: `http://127.0.0.1:8000/app/`
- API 문서: `http://127.0.0.1:8000/docs`

### 방법 B. 백엔드 + 정적 프론트 같이 실행

```powershell
.\run_stack.bat
```

이 경우:

- API: `http://127.0.0.1:8000`
- 정적 프론트: `http://127.0.0.1:5500`

### 방법 C. 프론트만 미리보기

```powershell
.\run_frontend.bat
```

주의:

- 프론트만 띄우면 실제 데이터 저장/조회는 안 됩니다.
- 백엔드가 같이 떠 있어야 합니다.

## 7. 웹 프론트엔드 설정

정적 웹앱은 `web/config.js`를 읽어 API 주소를 결정합니다.

로컬 기본값:

```js
window.EMOTION_TRACKER_CONFIG = {
  API_BASE_URL: "http://127.0.0.1:8000",
};
```

배포 시에는 이 파일을 바꿔야 합니다.

예:

```js
window.EMOTION_TRACKER_CONFIG = {
  API_BASE_URL: "https://api.example.com",
};
```

## 8. Cloudflare Pages에 프론트엔드 배포

정적 프론트엔드는 `web/` 폴더를 그대로 Cloudflare Pages에 올리면 됩니다.

공식 문서:

- Pages 시작 가이드:
  https://developers.cloudflare.com/pages/get-started/guide/
- Pages Custom Domains:
  https://developers.cloudflare.com/pages/configuration/custom-domains/

### 8-1. 배포 절차

1. Git 저장소를 GitHub 등에 올립니다.
2. Cloudflare Pages에서 새 프로젝트를 만듭니다.
3. 저장소를 연결합니다.
4. 프론트엔드 루트 디렉터리를 `web`으로 지정합니다.
5. 빌드 명령은 비워도 됩니다.
6. 배포합니다.

### 8-2. 커스텀 도메인 연결

예:

- `app.example.com` -> Cloudflare Pages
- `api.example.com` -> 백엔드 서버

그 다음 `web/config.js`의 `API_BASE_URL`을 `https://api.example.com`으로 바꿉니다.

## 9. 백엔드 배포

이 저장소의 백엔드는 FastAPI이므로 Cloudflare Pages에 직접 올리는 대상이 아닙니다.

권장 배포 대상:

- Render
- Railway
- Fly.io
- Google Cloud Run

실행 명령은 보통 아래와 같습니다.

```powershell
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

배포 후 공개 URL을 받으면 Cloudflare DNS에서 `api.example.com`으로 연결하면 됩니다.

## 10. API 목록

- `GET /health`
- `GET /storage`
- `GET /api/v1/meta`
- `GET /api/v1/users/{user_id}/hq`
- `POST /api/v1/users/{user_id}/records`
- `GET /api/v1/users/{user_id}/records`
- `GET /api/v1/users/{user_id}/analytics?period=today|week|month|all`

## 11. 중요한 현재 상태

현재 코드에서 이미 준비된 것:

- HQ 계산 로직
- 최빈 감정 / 시간대별 HQ / 요일별 HQ 분석
- FastAPI API 계층
- Firestore 저장소 어댑터
- 정적 HTML/CSS/JS 프론트엔드
- Cloudflare Pages에 올릴 수 있는 `web/` 폴더

현재 직접 검증하지 못한 것:

- 실제 Firestore 접속
- 실제 Cloudflare Pages 배포

이 두 가지는 서비스 계정 JSON과 실제 배포 계정이 있어야 최종 검증할 수 있습니다.

## 12. 다음으로 해야 할 일

1. Firebase 서비스 계정 JSON을 `secrets/firebase_service_account.json`에 넣기
2. `.env`를 Firestore 기준으로 작성하기
3. `.\run_backend.bat`로 Firestore 연결 확인하기
4. `.\run_stack.bat`로 정적 웹앱과 API 함께 확인하기
5. `web/config.js`를 실제 API 도메인으로 바꾸기
6. `web/` 폴더를 Cloudflare Pages에 배포하기
