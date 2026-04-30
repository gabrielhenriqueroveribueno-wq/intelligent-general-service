from functools import lru_cache

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

    # AI Provider (anthropic, gemini or groq)
    AI_PROVIDER: str = "groq"
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-opus-4-6"
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    CLAUDE_MAX_TOKENS: int = 1024
    CLAUDE_CLASSIFIER_MAX_TOKENS: int = 50

    # Mercado Pago
    MP_ACCESS_TOKEN: str = ""
    MP_PUBLIC_KEY: str = ""
    MP_WEBHOOK_SECRET: str = ""  # For validating MP webhook signatures

    # SMTP (Email)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True

    # Encryption (Fernet key for CPF, tokens)
    ENCRYPTION_KEY: str = ""

    # VAPID keys para Web Push (gere com: openssl ecparam -name prime256v1 -genkey)
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_SUBJECT: str = "mailto:contato@igs.com.br"

    # Sentry error tracking
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.05

    # Email — Resend API (preferred) or SMTP fallback
    RESEND_API_KEY: str = ""

    # SaaS billing plans (tenant monthly fee)
    SAAS_PLAN_STARTER_PRICE: float = 297.0
    SAAS_PLAN_PRO_PRICE: float = 497.0
    SAAS_BILLING_NOTIFICATION_URL: str = ""  # MP webhook callback URL

    # Row-Level Security
    RLS_ENABLED: bool = False  # Set True in production after running RLS migration
    RLS_APP_PASSWORD: str = "igs_app_secure_2026"
    RLS_WORKER_PASSWORD: str = "igs_worker_secure_2026"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Prometheus
    PROMETHEUS_ENABLED: bool = True

    # Super Admin (para seed inicial)
    SUPER_ADMIN_EMAIL: str = "admin@igs.com"
    SUPER_ADMIN_PASSWORD: str = "Admin@123456"
    SUPER_ADMIN_NAME: str = "IGS Admin"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
