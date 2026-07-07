"""
Centralized application configuration.

All environment-dependent values are read once here and imported
everywhere else via `get_settings()`. Nothing in the rest of the
codebase should call os.environ directly — this is the single
source of truth for config, which keeps the app 12-factor and easy
to test (settings can be overridden in tests without touching env vars).
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    app_debug: bool = True

    database_url: str
    redis_url: str = "redis://redis:6379/0"
    telegram_bot_token: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def _force_asyncpg_driver(cls, v: str) -> str:
        """
        Hosting platforms (Render, Heroku, ...) hand out a plain
        `postgres://` or `postgresql://` URL. SQLAlchemy's async engine
        needs the `+asyncpg` driver suffix — rewrite it here so both
        local .env values and platform-provided URLs work unchanged.
        """
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://") :]
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            v = "postgresql+asyncpg://" + v[len("postgresql://") :]
        return v


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — avoids re-parsing .env on every call."""
    return Settings()
