from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import secrets
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    """

    # Application settings
    APP_NAME: str = "Foxhole Backend API"
    DEBUG: bool = False

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # JWT settings
    JWT_SECRET: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379"  # Ensure this is correct

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "logs/app.log"

    # Storage settings
    USE_MOCK_STORAGE: bool = False  # Set this to False
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


settings = Settings()

# Explicitly set the REDIS_URL if it is not correctly loaded
if settings.REDIS_URL == "redis://your_actual_redis_host:6379":
    settings.REDIS_URL = "redis://localhost:6379"

# Print the loaded environment variables for debugging
print(f"Loaded REDIS_URL: {settings.REDIS_URL}")
print(f"Environment REDIS_URL: {os.getenv('REDIS_URL')}")
