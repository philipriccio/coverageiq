"""CoverageIQ API - Main application entry point."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import scripts, coverage

# Get CORS origins from environment variable or use defaults
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Initialize database
    await init_db()
    print("✓ Database initialized")
    yield
    # Shutdown: Cleanup if needed
    print("Shutting down...")


app = FastAPI(
    title="CoverageIQ API",
    description="AI-powered script coverage analysis tool",
    version="0.2.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scripts.router)
app.include_router(coverage.router)


@app.get("/")
def root():
    """API root - returns basic info."""
    return {
        "name": "CoverageIQ API",
        "version": "0.2.0",
        "description": "AI-powered script coverage analysis tool",
        "privacy_note": "Script content is processed in-memory only and never stored."
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.2.0",
        "privacy_compliant": True
    }


@app.get("/api/models")
def list_models():
    """List available LLM models for analysis."""
    return {
        "models": [
            {
                "id": "kimi-k2.5",
                "name": "Moonshot Kimi K2.5",
                "provider": "Moonshot AI",
                "default": True,
                "description": "Best for long-context analysis and creative writing assessment"
            },
            {
                "id": "claude-sonnet-4.5",
                "name": "Claude Sonnet 4.5",
                "provider": "Anthropic",
                "default": False,
                "description": "Alternative high-quality option"
            }
        ],
        "default": "kimi-k2.5"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
