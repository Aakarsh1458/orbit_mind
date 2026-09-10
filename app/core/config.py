import os
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "OrbitMind Backend"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/orbitmind"

    # AI Inference Mode: "mock" or "production"
    AI_MODE: str = "mock"

    # Storage Paths
    MODEL_CACHE_DIR: str = "./data/models"
    UPLOAD_DIR: str = "./data/uploads"
    PROCESSED_DIR: str = "./data/processed"
    RESULT_DIR: str = "./data/results"

    # Upload and processing constraints
    MAX_UPLOAD_SIZE_MB: int = 500
    ALLOWED_EXTENSIONS: List[str] = [".tif", ".tiff", ".png", ".jpg", ".jpeg"]

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    @field_validator("AI_MODE")
    @classmethod
    def validate_ai_mode(cls, v: str) -> str:
        mode = v.lower().strip()
        if mode not in ("mock", "production"):
            raise ValueError(f"Invalid AI_MODE: '{v}'. Must be either 'mock' or 'production'.")
        return mode

    def ensure_directories(self) -> None:
        """Ensure all runtime data directories exist."""
        for path_str in (self.MODEL_CACHE_DIR, self.UPLOAD_DIR, self.PROCESSED_DIR, self.RESULT_DIR):
            path = Path(path_str).resolve()
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
