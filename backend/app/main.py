import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables
from app.routers import upload, analysis, qa, report

app = FastAPI(
    title="Contract Risk Analyzer API",
    description="AI-powered contract risk analysis. Not legal advice.",
    version="1.0.0",
)

from app.config import get_settings as _get_settings
_settings = _get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins_list,
    allow_credentials=_settings.cors_origins_list != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(qa.router, prefix="/api")
app.include_router(report.router, prefix="/api")


@app.on_event("startup")
def startup():
    Path("./data/uploads").mkdir(parents=True, exist_ok=True)
    Path("./chroma").mkdir(parents=True, exist_ok=True)
    create_tables()


@app.get("/api/health")
def health():
    from app.config import get_settings
    settings = get_settings()
    return {"status": "ok", "mock_mode": settings.use_mock}
