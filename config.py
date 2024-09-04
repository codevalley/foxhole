from pydantic import BaseSettings

class Settings(BaseSettings):
    # JWT settings
    SECRET_KEY: str = "your-secret-key"  # Change this to a secure random key in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"

    # Redis settings
    REDIS_URL: str = "redis://localhost"

    class Config:
        env_file = ".env"

settings = Settings()