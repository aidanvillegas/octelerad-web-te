"""Application configuration using Pydantic settings."""

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Environment-driven application settings."""

    environment: str = Field(default="development", alias="ENVIRONMENT")
    db_url: str = Field(default="sqlite:///./dev.db", alias="DB_URL")
    jwt_secret: str = Field(default="dev-secret", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")

    @property
    def is_postgres(self) -> bool:
        return self.db_url.startswith(("postgresql://", "postgresql+psycopg://"))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance to avoid repeated env parsing."""

    return Settings()


settings = get_settings()
