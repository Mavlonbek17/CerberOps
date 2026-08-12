"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://cerberops:changeme_in_production@localhost:5432/cerberops"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:1.5b"

    # API Security
    api_key: str = ""

    # Scanner timeouts (seconds)
    nmap_timeout: int = 600
    nuclei_timeout: int = 900
    zap_timeout: int = 1200

    # ZAP
    zap_api_url: str = "http://localhost:8080"
    zap_api_key: str = ""

    # General
    log_level: str = "INFO"
    allow_internal_targets: bool = False
    workers: int = 2

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}


settings = Settings()
