from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Dict, List
import secrets
import os
from typing import Any


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    """

    # Application settings
    APP_NAME: str = "Foxhole Backend API"
    DEBUG: bool = False
    APP_ENV: str = "production"

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
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    RATE_LIMIT_REDIS_URL: str = (
        "redis://localhost:6379/1"  # Use a different DB than the main cache
    )

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "logs/app.log"

    # Storage settings
    USE_MOCK_STORAGE: bool = False  # Set this to False
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "foxhole"

    # Sidekick settings
    OPENAI_API_KEY: str = "put your key here"
    OPENAI_MODEL: str = "gpt-4o-mini"
    SIDEKICK_SYSTEM_PROMPT_FILE: str = "sidekick_prompt.txt"

    APP_VERSION: str = "0.1.0"

    # Rate limiting settings
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH_REGISTER: str = "10/minute"
    RATE_LIMIT_AUTH_TOKEN: str = "5/minute"
    RATE_LIMIT_WEBSOCKET: str = "1000/minute"  # High limit for WebSocket connections

    @property
    def rate_limits(self) -> Dict[str, str]:
        return {
            "default": self.RATE_LIMIT_DEFAULT,
            "auth_register": self.RATE_LIMIT_AUTH_REGISTER,
            "auth_token": self.RATE_LIMIT_AUTH_TOKEN,
            "websocket": self.RATE_LIMIT_WEBSOCKET,
        }

    @property
    def SIDEKICK_SYSTEM_PROMPT(self) -> str:
        try:
            with open(self.SIDEKICK_SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as file:
                return file.read().strip()
        except FileNotFoundError:
            print(
                f"Warning: {self.SIDEKICK_SYSTEM_PROMPT_FILE} not found. Using empty prompt."
            )
            return ""

    @classmethod
    def get_env_file(cls) -> List[str]:
        app_env = os.getenv("APP_ENV", "production").lower()
        env_files = [f".env.{app_env}", ".env"]
        print(f"Attempting to load environment from files: {env_files}")
        return env_files

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def __init__(self: "Settings", **kwargs: Any) -> None:
        env_files = self.get_env_file()
        super().__init__(_env_file=env_files, **kwargs)
        # Update os.environ with OPENAI_API_KEY if it's set
        if self.OPENAI_API_KEY and "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = self.OPENAI_API_KEY
        # self._log_loaded_values()

    def _log_loaded_values(self) -> None:
        print(f"Loaded APP_ENV: {self.APP_ENV}")
        print(f"Loaded RATE_LIMIT_DEFAULT: {self.RATE_LIMIT_DEFAULT}")
        print(f"Loaded RATE_LIMIT_AUTH_REGISTER: {self.RATE_LIMIT_AUTH_REGISTER}")
        print(f"Loaded RATE_LIMIT_AUTH_TOKEN: {self.RATE_LIMIT_AUTH_TOKEN}")
        print(f"Loaded RATE_LIMIT_WEBSOCKET: {self.RATE_LIMIT_WEBSOCKET}")
        print(f"Loaded DATABASE_URL: {self.DATABASE_URL}")
        print(f"Loaded REDIS_URL: {self.REDIS_URL}")
        print(f"Loaded MINIO_ENDPOINT: {self.MINIO_ENDPOINT}")
        print(f"Loaded SIDEKICK_SYSTEM_PROMPT_FILE: {self.SIDEKICK_SYSTEM_PROMPT_FILE}")
        print(f"SIDEKICK_SYSTEM_PROMPT length: {len(self.SIDEKICK_SYSTEM_PROMPT)}")


settings = Settings()

# Explicitly set the REDIS_URL if it is not correctly loaded
if settings.REDIS_URL == "redis://your_actual_redis_host:6379":
    settings.REDIS_URL = "redis://localhost:6379"

# Print the loaded environment variables for debugging
# print(f"Loaded APP_ENV: {settings.APP_ENV}")
# print(f"Loaded DATABASE_URL: {settings.DATABASE_URL}")
# print(f"Loaded REDIS_URL: {settings.REDIS_URL}")
# print(f"Loaded MINIO_ENDPOINT: {settings.MINIO_ENDPOINT}")
# print(f"SIDEKICK_SYSTEM_PROMPT length: {len(settings.SIDEKICK_SYSTEM_PROMPT)}")
# print(f"SIDEKICK_SYSTEM_PROMPT: {settings.SIDEKICK_SYSTEM_PROMPT}")
