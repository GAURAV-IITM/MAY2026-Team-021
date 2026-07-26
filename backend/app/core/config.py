from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

SUPPORTED_JWT_ALGORITHMS = frozenset({"HS256", "HS384", "HS512"})
LOCAL_ENVIRONMENTS = frozenset({"development", "local", "test"})
DEFAULT_JWT_SECRET = "change-this-development-secret-before-production"


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _normalize_database_url(value: str) -> str:
    """Select Psycopg 3 for provider-style PostgreSQL connection URLs."""
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


def _is_insecure_jwt_secret(value: str) -> bool:
    normalized = value.strip().lower()
    return (
        len(value) < 32
        or value == DEFAULT_JWT_SECRET
        or "change-this" in normalized
        or "replace-with" in normalized
    )


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Smart Library API")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = _as_bool(os.getenv("DEBUG"), default=False)
    api_v1_prefix: str = os.getenv("API_V1_PREFIX", "/api/v1")
    database_url: str = _normalize_database_url(
        os.getenv(
            "DATABASE_URL",
            f"sqlite:///{BASE_DIR / 'smart_library.db'}",
        )
    )
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:5174",
        ).split(",")
        if origin.strip()
    )
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", DEFAULT_JWT_SECRET)
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    refresh_token_expire_days: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "14")
    )
    account_invitation_expire_hours: int = int(
        os.getenv("ACCOUNT_INVITATION_EXPIRE_HOURS", "72")
    )
    frontend_base_url: str = os.getenv(
        "FRONTEND_BASE_URL",
        "http://localhost:5173",
    ).rstrip("/")

    def __post_init__(self) -> None:
        if self.jwt_algorithm not in SUPPORTED_JWT_ALGORITHMS:
            raise RuntimeError(f"Unsupported JWT algorithm: {self.jwt_algorithm}")

        if self.environment.lower() not in LOCAL_ENVIRONMENTS:
            if _is_insecure_jwt_secret(self.jwt_secret_key):
                raise RuntimeError(
                    "JWT_SECRET_KEY must be a unique secret of at least 32 characters "
                    "outside local development."
                )
            if self.access_token_expire_minutes <= 0:
                raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive.")
            if self.refresh_token_expire_days <= 0:
                raise RuntimeError("REFRESH_TOKEN_EXPIRE_DAYS must be positive.")
        if self.account_invitation_expire_hours <= 0:
            raise RuntimeError("ACCOUNT_INVITATION_EXPIRE_HOURS must be positive.")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
