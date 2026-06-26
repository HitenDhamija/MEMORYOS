"""
Core configurations and constants.
"""

import os
import json
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite:///./memoryos.db"
    
    # JWT
    secret_key: str = "dev-secret-key-change-in-production-min-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # CORS - read from env, fallback to localhost for dev
    cors_origins: str = '["http://localhost:3000","http://localhost:3001"]'
    
    # Environment
    environment: str = "development"
    debug: bool = False
    
    # App
    app_name: str = "MemoryOS API"
    app_version: str = "1.0.0"
    
    # File Upload Configuration
    upload_dir: str = "uploads"
    max_file_size: int = 100 * 1024 * 1024  # 100 MB
    allowed_extensions: dict = {
        "pdf": [".pdf"],
        "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
        "txt": [".txt"],
        "md": [".md", ".markdown"],
        "docx": [".docx"],
        "bookmark": [".url", ".webloc"],
    }

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string."""
        try:
            return json.loads(self.cors_origins)
        except (json.JSONDecodeError, TypeError):
            return ["http://localhost:3000", "http://localhost:3001"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
