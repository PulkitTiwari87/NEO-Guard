"""Application settings, read from environment variables (and an optional .env file)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # `model_*` field names are ours (MODEL_ENV, MODEL_DIR); disable pydantic's reserved prefix.
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env", extra="ignore", protected_namespaces=("settings_",)
    )

    database_url: str = Field(min_length=1)  # required: never hard-code credentials
    model_env: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"  # comma-separated
    model_dir: Path = REPO_ROOT / "ml" / "artifacts"
    active_model_version: str | None = None  # pin the served model; default = best status
    rate_limit_per_minute: int = Field(default=120, ge=0)  # 0 disables

    @property
    def sqlalchemy_url(self) -> str:
        """Accept plain postgresql:// URLs and select the installed psycopg (v3) driver."""
        url = self.database_url
        for prefix in ("postgresql://", "postgres://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix):]
        return url

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.model_env == "production"

    @model_validator(mode="after")
    def _no_wildcard_cors_in_production(self) -> Settings:
        if self.is_production and "*" in self.cors_origin_list:
            raise ValueError("CORS_ORIGINS must list explicit origins in production, not '*'")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
