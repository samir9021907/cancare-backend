"""
Application Configuration Module.

Reads environment variables from the `.env` file using pydantic-settings.
Provides sensible defaults for local development.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "CaneCare AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Security & JWT Token
    SECRET_KEY: str = "default_secret_key_change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database connection string (defaults to local SQLite database file)
    DATABASE_URL: str = "sqlite:///./canecare.db"

    # CORS (Cross-Origin Resource Sharing) origins allowed to make requests
    ALLOWED_ORIGINS: str = "*"

    # Upload and model storage folders
    UPLOAD_DIR: str = "./uploads"
    MODEL_DIR: str = "./models"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated origin strings into a list for FastAPI CORS middleware."""
        if not self.ALLOWED_ORIGINS or self.ALLOWED_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


# Create a single global settings instance to be used everywhere
settings = Settings()

# Ensure required runtime folders exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.MODEL_DIR, exist_ok=True)

