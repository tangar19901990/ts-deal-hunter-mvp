"""
Centralized application configuration.

All environment-dependent values are read once here and imported
everywhere else via `get_settings()`. Nothing in the rest of the
codebase should call os.environ directly — this is the single
source of truth for config, which keeps the app 12-factor and easy
to test (settings can be overridden in tests without touching env vars).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    app_debug: bool = True

    database_url: str
    redis_url: str = "redis://redis:6379/0"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — avoids re-parsing .env on every call."""
    return Settings()
