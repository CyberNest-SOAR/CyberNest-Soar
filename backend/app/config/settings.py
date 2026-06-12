# app/config/settings.py

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration loaded automatically from environment or .env."""

    # ==========================================
    # Core Infrastructure Connections
    # ==========================================
    database_url: str = Field(default="postgresql://postgres:postgres@localhost:5432/soar_db", validation_alias="DATABASE_URL")
    DATABASE_URL: str = Field(default="postgresql://postgres:postgres@localhost:5432/soar_db", validation_alias="DATABASE_URL")

    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    REDIS_URL: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    redis_cache_prefix: str = Field(default="cybernest", validation_alias="REDIS_CACHE_PREFIX")
    REDIS_CACHE_PREFIX: str = Field(default="cybernest", validation_alias="REDIS_CACHE_PREFIX")

    # ==========================================
    # Ingestion & Credentials Configurations
    # ==========================================
    google_client_secret_file: str = Field(default="client_secret.json", validation_alias="GOOGLE_CLIENT_SECRET_FILE")
    gmail_sync_folder: str = Field(default="INBOX", validation_alias="GMAIL_SYNC_FOLDER")
    gmail_max_results: int = Field(default=25, ge=1, le=500, validation_alias="GMAIL_MAX_RESULTS")
    token_directory: str = Field(default="token_files", validation_alias="GOOGLE_TOKEN_DIR")

    # Paths & Artifacts
    _package_root = Path(__file__).resolve().parents[2]
    _default_artifacts = _package_root / "artifacts"

    model_artifact_path: Path = Field(default=_default_artifacts / "phishing_model.joblib", validation_alias="MODEL_ARTIFACT_PATH")
    vectorizer_artifact_path: Path = Field(default=_default_artifacts / "tfidf_vectorizer.joblib", validation_alias="VECTORIZER_ARTIFACT_PATH")
    training_data_path: Path = Field(default=Path("data/data.csv"), validation_alias="TRAINING_DATA_PATH")

    # ==========================================
    # RAG / Vector Store Configuration
    # ==========================================
    qdrant_url: str = Field(default="http://localhost:6333", validation_alias="QDRANT_URL")
    QDRANT_URL: str = Field(default="http://localhost:6333", validation_alias="QDRANT_URL")

    qdrant_collection: str = Field(default="cybernest_router", validation_alias="QDRANT_COLLECTION")
    QDRANT_COLLECTION: str = Field(default="cybernest_router", validation_alias="QDRANT_COLLECTION")

    ollama_base_url: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_BASE_URL")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_BASE_URL")

    embedding_model: str = Field(default="nomic-embed-text", validation_alias="EMBEDDING_MODEL")
    EMBEDDING_MODEL: str = Field(default="nomic-embed-text", validation_alias="EMBEDDING_MODEL")
    
    routing_llm_model: str = Field(default="llama3:8b-instruct", validation_alias="ROUTING_LLM_MODEL")
    ROUTING_LLM_MODEL: str = Field(default="llama3:8b-instruct", validation_alias="ROUTING_LLM_MODEL")

    # ==========================================
    # OpenSearch / SOAR Configuration
    # ==========================================
    os_host: str = Field(default="https://localhost:9200", validation_alias="OS_HOST")
    OS_HOST: str = Field(default="https://localhost:9200", validation_alias="OS_HOST")

    os_port: int = Field(default=9200, validation_alias="OS_PORT")
    OS_PORT: int = Field(default=9200, validation_alias="OS_PORT")

    os_user: str = Field(default="admin", validation_alias="OS_USER")
    OS_USER: str = Field(default="admin", validation_alias="OS_USER")

    os_pass: str = Field(default="admin", validation_alias="OS_PASS")
    OS_PASS: str = Field(default="admin", validation_alias="OS_PASS")

    os_auth: str = Field(default="admin:SecretPassword", validation_alias="OS_AUTH")
    OS_AUTH: str = Field(default="admin:SecretPassword", validation_alias="OS_AUTH")

    # ==========================================
    # Integrations & Security Keys
    # ==========================================
    wazuh_url: str = Field(default="https://localhost:55000", validation_alias="WAZUH_URL")
    WAZUH_URL: str = Field(default="https://localhost:55000", validation_alias="WAZUH_URL")
    
    wazuh_user: str = Field(default="wazuh-wui", validation_alias="WAZUH_USER")
    WAZUH_USER: str = Field(default="wazuh-wui", validation_alias="WAZUH_USER")
    
    wazuh_pass: str = Field(default="MyS3cr37P450r.*-", validation_alias="WAZUH_PASS")
    WAZUH_PASS: str = Field(default="MyS3cr37P450r.*-", validation_alias="WAZUH_PASS")
    
    wazuh_key: str = Field(default="WAZUH_API_KEY", validation_alias="WAZUH_KEY")
    WAZUH_KEY: str = Field(default="WAZUH_API_KEY", validation_alias="WAZUH_KEY")

    vt_api_key: str = Field(default="VT_API_KEY", validation_alias="VT_API_KEY")
    VT_API_KEY: str = Field(default="VT_API_KEY", validation_alias="VT_API_KEY")
    
    abuse_key: str = Field(default="ABUSE_API_KEY", validation_alias="ABUSE_KEY")
    ABUSE_KEY: str = Field(default="ABUSE_API_KEY", validation_alias="ABUSE_KEY")
    
    nvd_api_key: str | None = Field(default=None, validation_alias="NVD_API_KEY")
    NVD_API_KEY: str | None = Field(default=None, validation_alias="NVD_API_KEY")
    
    otx_api_key: str = Field(default="", validation_alias="OTX_API_KEY")
    OTX_API_KEY: str = Field(default="", validation_alias="OTX_API_KEY")
    
    urlhaus_api_key: str = Field(default="", validation_alias="URLHAUS_API_KEY")
    URLHAUS_API_KEY: str = Field(default="", validation_alias="URLHAUS_API_KEY")

    misp_url: str = Field(default="https://localhost", validation_alias="MISP_URL")
    MISP_URL: str = Field(default="https://localhost", validation_alias="MISP_URL")
    
    misp_key: str = Field(default="MISP", validation_alias="MISP_KEY")
    MISP_KEY: str = Field(default="MISP", validation_alias="MISP_KEY")

    velociraptor_url: str = Field(default="https://localhost:8889", validation_alias="VELOCIRAPTOR_URL")
    VELOCIRAPTOR_URL: str = Field(default="https://localhost:8889", validation_alias="VELOCIRAPTOR_URL")
    
    velociraptor_api_key: str | None = Field(default=None, validation_alias="VELOCIRAPTOR_API_KEY")
    VELOCIRAPTOR_API_KEY: str | None = Field(default=None, validation_alias="VELOCIRAPTOR_API_KEY")

    thehive_url: str = Field(default="http://localhost:9000", validation_alias="THEHIVE_URL")
    THEHIVE_URL: str = Field(default="http://localhost:9000", validation_alias="THEHIVE_URL")
    
    thehive_api_key: str = Field(default="", validation_alias="THEHIVE_API_KEY")
    THEHIVE_API_KEY: str = Field(default="", validation_alias="THEHIVE_API_KEY")

    jwt_secret: str = Field(default="change_me_to_a_secure_random_string", validation_alias="JWT_SECRET")
    JWT_SECRET: str = Field(default="change_me_to_a_secure_random_string", validation_alias="JWT_SECRET")

    # Configuration Pipeline Mapping
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


# Cached instance for app-wide reuse
settings = Settings()