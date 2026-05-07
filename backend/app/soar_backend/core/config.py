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
    
    #Internal Threat Intel (MISP)
    MISP_URL: str = "https://localhost"
    MISP_KEY: str = "MISP"
    
    #Endpoint Forensic (Velociraptor)
    VELOCIRAPTOR_URL: str = "https://localhost:8889"
    VELOCIRAPTOR_API_KEY: str | None = None
    
    #System Config
    JWT_SECRET: str = "change_me_to_a_secure_random_string"
    DATABASE_URL: str = "postgresql://user:pass@localhost/soar_db"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

settings = Settings()
