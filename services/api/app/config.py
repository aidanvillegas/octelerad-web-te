"""Application configuration using Pydantic settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Environment-driven application settings."""

    environment: str = "development"
    db_url: str = "sqlite:///./dev.db"
    jwt_secret: str = "dev-secret"
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance to avoid repeated env parsing."""

    return Settings()


settings = get_settings()
