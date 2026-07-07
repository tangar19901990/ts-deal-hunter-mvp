"""
TS Deal Hunter AI — MVP entrypoint.

Step 1 scope: app boots, connects to Postgres, exposes a health check.
Search endpoints, models, and collectors are added in later steps.
"""

from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import engine

settings = get_settings()

app = FastAPI(
    title="TS Deal Hunter AI",
    description="Search engine for finding the cheapest listings across marketplaces.",
    version="0.1.0-mvp",
)


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
