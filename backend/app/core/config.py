"""Application configuration loaded from environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Core
    app_name: str = "Sadot Dogs CRM"
    environment: str = "development"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 720
    algorithm: str = "HS256"

    # Database
    database_url: str = "sqlite:///./sadot.db"

    # Object storage (local filesystem in phase 1; relative to the backend cwd)
    media_root: str = "media"

    # First admin (seeded on startup if missing)
    first_admin_email: str = "admin@sadot.local"
    first_admin_password: str = "admin1234"
    first_admin_name: str = "Admin"

    # CORS
    backend_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Public-facing site (used for QR intake links) + where the Next.js
    # frontend is mounted under nginx (matches next.config.js basePath).
    public_site_url: str = "https://sadot.lavit.io"
    frontend_base_path: str = "/crm"

    # External integration tokens (empty -> use mock adapters)
    whatsapp_api_token: str = ""
    payment_provider_key: str = ""
    signature_provider_key: str = ""
    smtp_host: str = ""
    smtp_port: str = ""
    smtp_user: str = ""
    smtp_password: str = ""
    monday_api_token: str = ""

    # Business / follow-up policy
    followup_days: int = 5
    home_subscription_monthly_price: int = 1000
    facility_total_amount: int = 7200

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
