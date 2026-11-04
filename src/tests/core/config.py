import os
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE") or BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    # Ограничение частоты попыток входа
    login_rate_limit_account: int = Field(default=5, ge=1)
    login_rate_limit_ip: int = Field(default=20, ge=1)
    login_rate_limit_window_seconds: int = Field(default=900, ge=1)

    # PostgreSQL
    postgres_host: str = Field(min_length=1)
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_db: str = Field(min_length=1)
    postgres_user: str = Field(min_length=1)
    postgres_password: SecretStr = Field(min_length=1)

    # Redis
    redis_host: str = Field(min_length=1)
    redis_port: int = Field(default=6379, ge=1, le=65535)
    redis_db: int = Field(default=0, ge=0)

    # API
    service_url: str

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()
