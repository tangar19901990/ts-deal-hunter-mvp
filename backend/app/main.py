"""
TS Deal Hunter AI — MVP entrypoint.

Step 1 scope: app boots, connects to Postgres, exposes a health check.
Search endpoints, models, and collectors are added in later steps.
"""

import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import import_listing, search
from app.core.config import get_settings
from app.db.session import engine
from app.scripts.seed import seed
from app.telegram.bot import start_bot_polling

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


@app.on_event("startup")
async def launch_telegram_bot() -> None:
    """
    Starts the Telegram bot's long-polling loop as a background task
    so it runs alongside the API in the same process — no separate
    worker service needed for the MVP. No-ops if TELEGRAM_BOT_TOKEN
    isn't configured (see app/telegram/bot.py).
    """
    asyncio.create_task(start_bot_polling())


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
