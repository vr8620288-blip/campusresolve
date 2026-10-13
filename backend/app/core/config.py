"""
Application configuration.

Reads settings from environment variables / a .env file (see .env.example).
Defaults are safe for local development with SQLite so the project can be
run without installing PostgreSQL first.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "CampusResolve API"

    DATABASE_URL: str = "sqlite:///./campus_resolve.db"

    JWT_SECRET_KEY: str = "dev-secret-key-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    UPLOAD_DIRECTORY: str = "./uploads"
    MAX_UPLOAD_MB: int = 5

    CORS_ORIGINS: str = "http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000,*"

    @property
    def cors_origin_list(self) -> List[str]:
        raw = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        return raw or ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
