from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes.emotions import router as emotion_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.meta import router as meta_router
from backend.app.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title="Emotion Tracker API",
    version="0.1.0",
    description="Streamlit 프론트엔드가 호출하는 감정 기록/HQ 분석 API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(meta_router)
app.include_router(emotion_router)


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/app/")


app.mount("/app", StaticFiles(directory="web", html=True), name="web")
