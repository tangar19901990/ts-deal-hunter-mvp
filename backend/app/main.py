"""
TS Deal Hunter AI — MVP entrypoint.

Step 1 scope: app boots, connects to Postgres, exposes a health check.
Search endpoints, models, and collectors are added in later steps.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import import_listing, search
from app.core.config import get_settings
from app.db.session import engine
from app.scripts.seed import seed

settings = get_settings()

app = FastAPI(
    title="TS Deal Hunter AI",
    description="Search engine for finding the cheapest listings across marketplaces.",
    version="0.1.0-mvp",
)

# MVP CORS: allow any origin. The frontend is deployed on GitHub Pages
# (a different origin than the API), so this is required for it to work.
# Tighten to a specific origin list before this leaves MVP status.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(search.router, tags=["search"])
app.include_router(import_listing.router, tags=["import"])


@app.on_event("startup")
async def seed_sample_data() -> None:
    """
    MVP-only: auto-seed sample listings on every startup so the live
    demo always has data, even on Render's free tier (no shell access
    to run the seed script manually). Idempotent — skips rows that
    already exist. Remove once a real collector populates the DB.
    """
    await seed()


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """Basic liveness + DB connectivity check."""
    db_ok = True
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "env": settings.app_env,
        "database": "connected" if db_ok else "unreachable",
    }
