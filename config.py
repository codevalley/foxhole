from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Your settings here
    DATABASE_URL: str = "sqlite:///./test.db"
    # Add other configuration settings as needed

    class Config:
        env_file = ".env"

settings = Settings()