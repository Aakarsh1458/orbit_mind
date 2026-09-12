import os
from pathlib import Path
from typing import List, Optional, Union
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
    ALLOWED_EXTENSIONS: List[str] = [".tif", ".tiff", ".png", ".jpg", ".jpeg", ".webp"]

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # LLM Orchestration
    DEFAULT_LLM_PROVIDER: str = "gemini"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    HF_TOKEN: Optional[str] = None
    HF_MODEL_ID: Optional[str] = None
    LOCAL_LLM_URL: str = "http://localhost:11434/v1"
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "nvidia/nemotron-3.5-lightning:free"
    NEMOTRON_API_KEY: Optional[str] = None
    NEMOTRON_MODEL: str = "nvidia/nemotron-3.5-lightning:free"

    # Multi-Model Workload Specialization & Tiering
    LLM_STAGE_QUERY_UNDERSTANDING_PRIMARY_PROVIDER: str = "gemini"
    LLM_STAGE_QUERY_UNDERSTANDING_PRIMARY_MODEL: str = "gemini-1.5-flash"
    LLM_STAGE_QUERY_UNDERSTANDING_FALLBACK_PROVIDER: str = "openrouter"
    LLM_STAGE_QUERY_UNDERSTANDING_FALLBACK_MODEL: str = "meta-llama/llama-3.3-70b-instruct"

    LLM_STAGE_TASK_PLANNING_PRIMARY_PROVIDER: str = "openrouter"
    LLM_STAGE_TASK_PLANNING_PRIMARY_MODEL: str = "anthropic/claude-3.5-sonnet"
    LLM_STAGE_TASK_PLANNING_FALLBACK_PROVIDER: str = "gemini"
    LLM_STAGE_TASK_PLANNING_FALLBACK_MODEL: str = "gemini-1.5-pro"

    LLM_STAGE_VQA_PRIMARY_PROVIDER: str = "gemini"
    LLM_STAGE_VQA_PRIMARY_MODEL: str = "gemini-1.5-pro"
    LLM_STAGE_VQA_FALLBACK_PROVIDER: str = "openrouter"
    LLM_STAGE_VQA_FALLBACK_MODEL: str = "openai/gpt-4o"

    LLM_STAGE_RESPONSE_GENERATION_PRIMARY_PROVIDER: str = "gemini"
    LLM_STAGE_RESPONSE_GENERATION_PRIMARY_MODEL: str = "gemini-1.5-flash"
    LLM_STAGE_RESPONSE_GENERATION_FALLBACK_PROVIDER: str = "openrouter"
    LLM_STAGE_RESPONSE_GENERATION_FALLBACK_MODEL: str = "deepseek/deepseek-chat"

    # Circuit Breaker & Failover Policy
    LLM_CIRCUIT_BREAKER_FAIL_THRESHOLD: int = 3
    LLM_CIRCUIT_BREAKER_RESET_SECONDS: int = 60

    # Agent Loop & Policies
    MAX_AGENT_STEPS: int = 8
    MAX_RETRIES: int = 2
    REQUEST_TIMEOUT_SECONDS: int = 120
    ENABLE_FALLBACK: bool = True
    ENABLE_TOOL_CALLING: bool = True
    DEVICE: str = "auto"
    MAX_CONVERSATION_MESSAGES: int = 20

    def get_effective_device(self) -> str:
        """Determines computation device based on configuration and hardware."""
        if self.DEVICE != "auto":
            return self.DEVICE
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

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

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def resolve_local_database_url(cls, v: str) -> str:
        # If default docker host 'db' is specified but running on bare metal, fallback to SQLite
        if "@db:5432" in v and not os.path.exists("/.dockerenv") and not os.environ.get("RUNNING_IN_DOCKER"):
            return "sqlite+aiosqlite:///./data/orbitmind.db"
        return v

    def ensure_directories(self) -> None:
        """Ensure all runtime data directories exist."""
        for path_str in (self.MODEL_CACHE_DIR, self.UPLOAD_DIR, self.PROCESSED_DIR, self.RESULT_DIR):
            path = Path(path_str).resolve()
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
