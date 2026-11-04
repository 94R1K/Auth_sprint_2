from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    jwt_private_key_path: Path
    jwt_public_key_path: Path

    # Ограничение частоты попыток входа
    login_rate_limit_account: int = Field(default=15, ge=1)
    login_rate_limit_ip: int = Field(default=30, ge=1)
    login_rate_limit_window_seconds: int = Field(default=600, ge=1)

    # SQLAlchemy
    sqlalchemy_log_level: Literal["INFO", "WARNING"] = "WARNING"
    sqlalchemy_hide_parameters: bool = True

    # Название проекта
    project_name: str = Field(min_length=1)

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

    access_token_ttl: int = Field(default=900, ge=1)
    refresh_token_ttl: int = Field(default=60 * 60 * 24 * 30, ge=1)

    superuser_login: str
    superuser_password: str

    @property
    def jwt_private_key(self) -> str:
        return self.jwt_private_key_path.read_text()

    @property
    def jwt_public_key(self) -> str:
        return self.jwt_public_key_path.read_text()

    @property
    def postgres_url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()
