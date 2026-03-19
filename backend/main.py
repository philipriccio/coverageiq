"""CoverageIQ API - Main application entry point."""
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, init_db
from app.models import AnalysisJob, JobStatus
from app.routers import coverage, scripts

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
APP_VERSION = "0.3.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="CoverageIQ API",
    description="AI-powered script coverage analysis tool",
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scripts.router)
app.include_router(coverage.router)


@app.get("/")
def root():
    return {
        "name": "CoverageIQ API",
        "version": APP_VERSION,
        "description": "AI-powered script coverage analysis tool",
        "privacy_note": "Script content is processed in-memory only and never stored.",
    }


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    from datetime import datetime, timedelta

    status = {"status": "healthy", "version": APP_VERSION, "privacy_compliant": True}
    try:
        await db.execute(select(1))
        status["database"] = "connected"
    except Exception as exc:
        status["database"] = f"error: {exc}"
        status["status"] = "degraded"

    try:
        stuck_threshold = datetime.utcnow() - timedelta(minutes=10)
        result = await db.execute(
            select(func.count(AnalysisJob.id)).where(
                AnalysisJob.status.in_([JobStatus.QUEUED, JobStatus.PROCESSING]),
                AnalysisJob.updated_at < stuck_threshold,
            )
        )
        stuck_count = result.scalar() or 0
        status["stuck_jobs"] = stuck_count
        if stuck_count > 0:
            status["status"] = "degraded"
    except Exception as exc:
        status["stuck_jobs_check"] = f"error: {exc}"
    return status


@app.get("/api/models")
def list_models():
    return {
        "models": [
            {
                "id": "gpt-4.1",
                "name": "OpenAI GPT-4.1",
                "provider": "OpenAI",
                "default": True,
                "description": "Primary high-quality long-form analysis model",
            },
            {
                "id": "claude-sonnet-4-5",
                "name": "Claude Sonnet 4.5",
                "provider": "Anthropic",
                "default": False,
                "description": "Fallback model if OpenAI fails",
            },
        ],
        "default": "gpt-4.1",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
