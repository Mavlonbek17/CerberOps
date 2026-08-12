"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    postgres_user: str = "cerberops"
    postgres_password: str = "changeme_in_production"
    postgres_db: str = "cerberops"
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

    # ── AI Features ───────────────────────────────────────────
    # False Positive Filter: AI re-reviews low/medium findings before they're
    # saved and drops obvious noise (WAF block pages, generic 403s, etc.)
    ai_triage_enabled: bool = True
    ai_triage_severities: str = "low,medium"

    # Smart Recon: fingerprint the target and let AI narrow scanner
    # templates/ports before running the full scan
    ai_smart_recon_enabled: bool = True
    ai_recon_timeout: int = 15

    # PoC Generator: write a safe verification script for confirmed
    # high/critical findings
    ai_poc_enabled: bool = True

    # Chat: max findings/characters fed into the chat context window
    ai_chat_max_findings: int = 40

    # ── Notifications ──────────────────────────────────────────────
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "cerberops@localhost"
    notification_email_to: str = ""

    # ── Scheduler ─────────────────────────────────────────────────
    scheduler_enabled: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}


settings = Settings()
