"""
SmartCampus AI — Application Configuration

All settings are loaded from environment variables.
Secrets (SMTP password, JWT secret) are NEVER hard-coded or logged.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """
    Central configuration loaded exclusively from environment variables / .env file.
    Sensitive fields use repr=False to prevent accidental exposure in logs or repr().
    """

    # --- Application ---
    app_name: str = "SmartCampus AI"
    app_env: str = "development"
    secret_key: str = Field(default="change-me-in-production", repr=False)
    debug: bool = True

    # --- Database ---
    database_url: str = "sqlite:///./smartcampus.db"

    # --- SMTP / Email ---
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = Field(default="", repr=False)  # NEVER expose this
    email_from: str = ""
    email_from_name: str = "SmartCampus AI"
    email_enabled: bool = False  # Defaults OFF — must be explicitly enabled

    # --- Voice Agent ---
    voice_agent_id: str = "-P2vKX2Tc3Zk_oW6XcnI"
    voice_agent_fallback_id: str = "P2YJQU8i3wOC75sAJ3f"

    # --- JWT ---
    jwt_secret_key: str = Field(default="change-me-in-production", repr=False)
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440  # 24 hours

    @property
    def is_email_configured(self) -> bool:
        """Check whether SMTP credentials are actually provided."""
        return bool(
            self.smtp_username
            and self.smtp_password
            and self.email_from
            and self.email_enabled
        )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton — reads .env once at startup."""
    return Settings()
