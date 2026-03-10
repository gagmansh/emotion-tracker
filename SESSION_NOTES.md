# Session Notes

## Project

- Name: `emotion_tracker`
- Working directory: `C:\Users\prist\OneDrive\바탕 화면\emotion_tracker`

## Current Target Architecture

- Frontend:
  - Static HTML/CSS/JS site in `web/`
  - Main files:
    - `web/index.html`
    - `web/styles.css`
    - `web/app.js`
    - `web/config.js`
- Backend:
  - FastAPI in `backend/app/main.py`
  - API routes in `backend/app/api/routes/`
- Storage:
  - Production target: Firebase Firestore
  - Fallback/dev support: JSON repository still exists

## Important Backend Files

- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/core/dependencies.py`
- `backend/app/repositories/firestore_store.py`
- `backend/app/repositories/json_store.py`
- `backend/app/services/emotion_service.py`
- `backend/app/api/routes/emotions.py`
- `backend/app/api/routes/health.py`
- `backend/app/api/routes/meta.py`

## Important Frontend Files

- `web/index.html`
- `web/styles.css`
- `web/app.js`
- `web/config.js`
- `web/config.example.js`

## Current API Surface

- `GET /health`
- `GET /storage`
- `GET /api/v1/meta`
- `GET /api/v1/users/{user_id}/hq`
- `POST /api/v1/users/{user_id}/records`
- `GET /api/v1/users/{user_id}/records`
- `GET /api/v1/users/{user_id}/analytics?period=today|week|month|all`

## Current Local Run Commands

- Backend only:
  - `.\run_backend.bat`
- Static frontend only:
  - `.\run_frontend.bat`
- Full local stack:
  - `.\run_stack.bat`
- Backend direct:
  - `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload`
- Static frontend direct:
  - `python -m http.server 5500 --directory web`

## Current Local URLs

- Backend API: `http://127.0.0.1:8000`
- Backend-served web app: `http://127.0.0.1:8000/app/`
- Static frontend preview: `http://127.0.0.1:5500`
- API docs: `http://127.0.0.1:8000/docs`

## Verified State

- Backend compile check passed
- Static frontend files exist and are served
- `GET /api/v1/meta` returns emotion metadata
- `GET /app/` returns the web frontend
- Temporary local static server on port `5500` returned `200`
- Web frontend content check for `Emotion Tracker` passed
- Real Firestore connection verified with service account JSON
- `/storage` reports `backend=firestore`
- `/api/v1/users/demo_user/hq` returned `200`
- End-to-end Firestore write/read test passed through running API
- Temporary Firestore integration test record was cleaned up after verification

## Not Yet Fully Verified

- Real Cloudflare Pages deployment
- Real custom domain routing for:
  - `app.example.com`
  - `api.example.com`

## Required For Firestore

Need user-provided file:

- `secrets/firebase_service_account.json`

Need `.env` values:

- `APP_STORAGE_BACKEND=firestore`
- `FIREBASE_SERVICE_ACCOUNT_PATH=./secrets/firebase_service_account.json`
- `FIRESTORE_COLLECTION_NAME=emotion_records`
- `APP_CORS_ORIGINS=...`

## Deployment Direction

- Frontend:
  - Deploy `web/` to Cloudflare Pages
- Backend:
  - Deploy FastAPI separately (Render / Railway / Fly.io / Cloud Run)
- Domain:
  - Cloudflare custom domains in front
- Frontend config:
  - Set `web/config.js` `API_BASE_URL` to deployed backend URL

## Next Recommended Tasks

1. Get real Firebase service account JSON from the user.
2. Switch backend to Firestore and verify create/read/analytics on real data.
3. Deploy backend to a public Python host.
4. Deploy `web/` to Cloudflare Pages.
5. Point custom domains and update `web/config.js`.
6. Add authentication if this is for real public users.

## Resume Prompt

Use this in a new Codex CLI session:

```text
Continue work on emotion_tracker.
Read SESSION_NOTES.md first.
Current goal: connect Firestore and verify the static web frontend end-to-end.
Check these files first:
- backend/app/main.py
- backend/app/repositories/firestore_store.py
- web/app.js
- README.md
```
