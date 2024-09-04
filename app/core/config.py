from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MinIO settings
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    MINIO_HOST: str = "localhost:9000"
    MINIO_SECURE: bool = False

    # JWT settings
    SECRET_KEY: str = "your-secret-key"  # Change this to a secure random key in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"

    # Redis settings
    REDIS_URL: str = "redis://localhost"

    class Config:
        env_file = ".env"

settings = Settings()