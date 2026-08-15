# FastAPI application entry point
# Configures lifespan events (startup/shutdown), CORS middleware, and includes API routers
"""
MeetQ Backend — FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload --port 8000
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import engine, Base
import app.models  # noqa: F401

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    - On startup: create tables if they don't exist (dev convenience).
    - On shutdown: dispose the database engine cleanly.
    """
    # --- Startup ---
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Database tables ready")

    yield

    # --- Shutdown ---
    await engine.dispose()
    print("✓ Database connection closed")


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allows your frontend (React/Next.js) to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "ok",
        "app": settings.app_name,
    }