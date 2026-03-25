from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me-in-production"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_VERSION: str = "1.0.0"
    APP_TITLE: str = "IGS - Intelligent General Service"
    APP_DESCRIPTION: str = "SaaS de atendimento inteligente via WhatsApp para instituições"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://igs_user:igs_password@localhost:5432/igs_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # JWT
    JWT_SECRET_KEY: str = "change-me-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # WhatsApp
    WHATSAPP_APP_SECRET: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "igs-verify-token"
    WHATSAPP_API_URL: str = "https://graph.facebook.com/v20.0"

    # Claude API
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-opus-4-6"
    CLAUDE_MAX_TOKENS: int = 1024
    CLAUDE_CLASSIFIER_MAX_TOKENS: int = 50

    # Encryption (Fernet key for CPF, tokens)
    ENCRYPTION_KEY: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Prometheus
    PROMETHEUS_ENABLED: bool = True

    # Super Admin (para seed inicial)
    SUPER_ADMIN_EMAIL: str = "admin@igs.com"
    SUPER_ADMIN_PASSWORD: str = "Admin@123456"
    SUPER_ADMIN_NAME: str = "IGS Admin"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
