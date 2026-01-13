import os
from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application configuration."""

    database_url: str = os.getenv("PPTO_DATABASE_URL", "sqlite:///./ppto.db")
    log_level: str = os.getenv("PPTO_LOG_LEVEL", "INFO")
    app_name: str = "PPTO API"

    class Config:
        env_prefix = "PPTO_"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
