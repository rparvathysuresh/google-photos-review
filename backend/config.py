"""
Configuration module for the Discovery Engine backend.

Centralizes all environment configuration using Pydantic Settings.
Loads from .env file and validates required variables at startup.
"""

import logging
import json
import sys
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # ── Required ──────────────────────────────────────────────
    GROQ_API_KEY: str = Field(
        ...,
        description="API key for Groq LLM inference (Llama 3 / Mixtral)"
    )

    # ── Storage ──────────────────────────────────────────────
    DATA_DIR: str = Field(
        default="data",
        description="Base directory for local data storage"
    )

    # ── Database ──────────────────────────────────────────────
    @property
    def DATABASE_URL(self) -> str:
        return f"sqlite:///{self.DATA_DIR}/discovery.db"

    # ── Vector Store ──────────────────────────────────────────
    @property
    def CHROMA_PERSIST_DIR(self) -> str:
        return f"{self.DATA_DIR}/chroma"

    # ── Optional: Source Adapter Credentials ──────────────────
    REDDIT_CLIENT_ID: Optional[str] = Field(
        default=None,
        description="Reddit API client ID (for PRAW)"
    )
    REDDIT_CLIENT_SECRET: Optional[str] = Field(
        default=None,
        description="Reddit API client secret (for PRAW)"
    )
    REDDIT_USER_AGENT: Optional[str] = Field(
        default="DiscoveryEngine/1.0",
        description="Reddit API user agent string"
    )
    YOUTUBE_API_KEY: Optional[str] = Field(
        default=None,
        description="YouTube Data API v3 key"
    )
    PLAYSTORE_LANG: Optional[str] = Field(
        default="en",
        description="Language for Google Play Store review scraping"
    )

    # ── Server ────────────────────────────────────────────────
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    DEBUG: bool = Field(default=True, description="Debug mode")
    BACKEND_CORS_ORIGINS: str = Field(
        default="http://localhost:5173",
        description="Comma-separated list of allowed CORS origins"
    )

    # ── Groq Model Config ─────────────────────────────────────
    GROQ_MODEL: str = Field(
        default="qwen/qwen3.8-27b",
        description="Groq model ID for extraction and RAG"
    )

    # ── Embedding Config ──────────────────────────────────────
    EMBEDDING_MODEL: str = Field(
        default="BAAI/bge-large-en-v1.5",
        description="HuggingFace model ID for BGE embeddings"
    )
    EMBEDDING_BATCH_SIZE: int = Field(
        default=64,
        description="Batch size for local embedding generation"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


def setup_logging(debug: bool = True) -> None:
    """Configure structured JSON logging."""

    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if record.exc_info and record.exc_info[0] is not None:
                log_entry["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_entry)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_settings() -> Settings:
    """
    Create and validate settings.
    Fails fast with a clear error if required variables are missing.
    """
    try:
        return Settings()
    except Exception as e:
        print(f"\n{'='*60}")
        print("CONFIGURATION ERROR")
        print(f"{'='*60}")
        print(f"\n{e}")
        print(f"\nEnsure your .env file exists and contains all required variables.")
        print(f"See .env.example for the required configuration.\n")
        sys.exit(1)


# Singleton settings instance
settings = get_settings()
