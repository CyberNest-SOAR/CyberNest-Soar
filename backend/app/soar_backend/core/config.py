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
    WAZUH_KEY: str = "eyJhbGciOiJFUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ3YXp1aCIsImF1ZCI6IldhenVoIEFQSSBSRVNUIiwibmJmIjoxNzc4MDk4MjIxLCJleHAiOjE3NzgwOTkxMjEsInN1YiI6IndhenVoLXd1aSIsInJ1bl9hcyI6ZmFsc2UsInJiYWNfcm9sZXMiOlsxXSwicmJhY19tb2RlIjoid2hpdGUifQ.AeUdWFWABXE1jiMNpWUWXRvaBzhC-L1KpB5sTZpiBAajrsG5lB8IRqMlu5spiY-T-hj_k7XlvfWL0FTa42BdzUBGAG3Dp81eBPLPj8HorJStc8M5Eot8VPohpNdikhSRjIif4WLcbxT9VRBR_4oTyuXgNRB70gnYLrehBpECNZmTkZ2c" # For compatibility with your previous code
    
    #External Enrichment APIs
    VT_API_KEY: str = "c5a229b21c609c6b29b856dc2287f0bd1545e73c2efa103237f130b14d0fded3"
    ABUSE_KEY: str = "ffa04ecd1041ed991eefcaf3372baad4061f1cf04286b55c8d44ffb1f3d9fac6eb069d5e19ef889b"
    NVD_API_KEY: str | None = None # Optional, but recommended for NVD/CVSS lookups
    
    #Internal Threat Intel (MISP)
    MISP_URL: str = "https://localhost"
    MISP_KEY: str = "Pa6EHBiKTWwLIGevh0tGYKYVTUAQDiv8WGLHssRl"
    
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
