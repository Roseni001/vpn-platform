from functools import lru_cache

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Runtime configuration loaded from environment variables and .env files."""

    app_name: str = "vpn-platform"
    environment: str = "local"
    log_level: str = "INFO"

    wg_easy_base_url: AnyHttpUrl = Field(default="http://localhost:51821")
    wg_easy_timeout_seconds: float = Field(default=10.0, gt=0)
    wg_easy_api_token: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_config() -> Config:
    """Return cached application configuration."""
    return Config()
