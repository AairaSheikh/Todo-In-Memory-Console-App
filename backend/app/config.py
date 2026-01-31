"""Application configuration."""

from pydantic_settings import BaseSettings
from pathlib import Path
import os

# Load .env file explicitly
from dotenv import load_dotenv
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    environment: str = "development"
    openai_api_key: str

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()
