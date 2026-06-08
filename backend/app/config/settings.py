# app/config/settings.py

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration loaded automatically from .env or environment."""

    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/soar_db",
        description="PostgreSQL connection URL",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL used for shared cache entries",
    )
    redis_cache_prefix: str = Field(
        default="cybernest",
        description="Prefix applied to Redis cache keys",
    )
    google_client_secret_file: str = Field(
        default="client_secret.json",
        description="Path to Google OAuth client secret JSON file",
    )
    gmail_sync_folder: str = Field(
        default="INBOX",
        description="Gmail folder label to read when syncing",
    )
    gmail_max_results: int = Field(
        default=25,
        ge=1,
        le=500,
        description="Maximum number of emails to fetch per sync",
    )
    token_directory: str = Field(
        default="token_files",
        description="Directory for cached Google OAuth tokens",
    )
    # Resolve artifacts directory relative to the package root so settings
    # are not sensitive to the current working directory when the app is run.
    _package_root = Path(__file__).resolve().parents[2]
    _default_artifacts = _package_root / "artifacts"

    model_artifact_path: Path = Field(
        default=_default_artifacts / "phishing_model.joblib",
        description="Location of phishing ML model artifact",
    )
    vectorizer_artifact_path: Path = Field(
        default=_default_artifacts / "tfidf_vectorizer.joblib",
        description="Location of persisted TF-IDF vectorizer (tfidf_vectorizer.joblib)",
    )
    training_data_path: Path = Field(
        default=Path("data/data.csv"),
        description="Default CSV dataset for training the phishing detector",
    )

    # RAG/Vector Store Configuration
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant vector database URL",
    )
    qdrant_collection: str = Field(
        default="cybernest_router",
        description="Name of the Qdrant collection for semantic routing",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama local LLM service base URL",
    )
    embedding_model: str = Field(
        default="nomic-embed-text",
        description="Embedding model to use in Ollama",
    )
    routing_llm_model: str = Field(
        default="llama3:8b-instruct",
        description="LLM model to use for query generation in Ollama",
    )

    # Enable `.env` loading automatically
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Cached instance for app-wide reuse
settings = Settings()
