import os
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _environment_file() -> str:
    environment = os.getenv("APP_ENV", "development").strip().lower()
    if environment in {"development", "qa", "production"}:
        return f".env.{environment}"
    return ".env"


class Settings(BaseSettings):
    app_env: Literal["development", "qa", "production"] = "development"
    database_url: str = (
        "postgresql://postgres:1234@localhost:5432/postgres"
    )
    jwt_secret_key: str = "development-only-change-this-secret"
    access_token_expire_minutes: int = 30
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(extra="ignore")

    @model_validator(mode="after")
    def validate_production_secret(self) -> "Settings":
        if self.app_env == "production" and (
            len(self.jwt_secret_key) < 32
            or self.jwt_secret_key.startswith("replace-with-")
            or self.jwt_secret_key == "development-only-change-this-secret"
        ):
            raise ValueError(
                "Set JWT_SECRET_KEY to a unique secret of at least 32 characters in production."
            )
        return self

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings(_env_file=_environment_file())
