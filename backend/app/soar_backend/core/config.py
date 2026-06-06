from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    #OpenSearch (Core Data)
    OS_HOST: str = "https://localhost:9200"
    OS_AUTH: str = "admin:SecretPassword"
    
    #Wazuh (SIEM & Agent Management)
    #Used for headers and token generation
    WAZUH_URL: str = "https://localhost:55000"
    WAZUH_USER: str = "wazuh-wui"
    WAZUH_PASS: str = "MyS3cr37P450r.*-"
    WAZUH_KEY: str = "WAZUH_API_KEY" # For compatibility with your previous code
    
    #External Enrichment APIs
    VT_API_KEY: str = "VT_API_KEY"
    ABUSE_KEY: str = "ABUSE_API_KEY"
    NVD_API_KEY: str | None = None # Optional, but recommended for NVD/CVSS lookups
    OTX_API_KEY: str = "" # AlienVault OTX API key
    URLHAUS_API_KEY: str = "" # abuse.ch Auth-Key for URLhaus API

    #Risk scoring model artifacts
    _package_root = Path(__file__).resolve().parents[1]
    _default_artifacts = _package_root / "artifacts"
    _risk_scoring_dir = _default_artifacts / "Risk scoring model"
    RISK_MODEL_PATH: Path = _risk_scoring_dir / "base_xgb_model_pipeline.joblib"
    RISK_LABEL_ENCODER_PATH: Path = _risk_scoring_dir / "label_encoder.joblib"
    
    #Internal Threat Intel (MISP)
    MISP_URL: str = "https://localhost"
    MISP_KEY: str = "MISP"
    
    #Endpoint Forensic (Velociraptor)
    VELOCIRAPTOR_URL: str = "https://localhost:8889"
    VELOCIRAPTOR_API_KEY: str | None = None
    
    #TheHive (Case Management)
    THEHIVE_URL: str = "http://localhost:9000"
    THEHIVE_API_KEY: str = ""

    #System Config
    JWT_SECRET: str = "change_me_to_a_secure_random_string"
    DATABASE_URL: str = "postgresql://user:pass@localhost/soar_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_PREFIX: str = "cybernest"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

settings = Settings()
