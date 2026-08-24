from pydantic_settings import BaseSettings, SettingsConfigDict


_base_config = SettingsConfigDict(
    env_file="./.env",
    env_ignore_empty=True,
    extra="ignore",
)


class AppSettings(BaseSettings):
    APP_NAME: str = "FastShip"
    APP_DOMAIN: str = "localhost:8000"
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    TASK_EXECUTION_MODE: str = "direct"  # "direct" or "celery"

    model_config = _base_config


class DatabaseSettings(BaseSettings):
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_USERNAME: str = ""

    model_config = _base_config

    @property
    def POSTGRES_URL(self):
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}"
            f"/{self.POSTGRES_DB}"
        )

    def REDIS_URL(self, db):
        # Authenticated Redis, e.g. external/TLS connection
        if self.REDIS_USERNAME and self.REDIS_PASSWORD:
            return (
                f"rediss://{self.REDIS_USERNAME}:{self.REDIS_PASSWORD}"
                f"@{self.REDIS_HOST}:{self.REDIS_PORT}/{db}"
                "?ssl_cert_reqs=CERT_NONE"
            )

        # Unauthenticated Redis, e.g. Render internal connection
        return (
            f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{db}"
        )


class SecuritySettings(BaseSettings):
    JWT_SECRET: str
    JWT_ALGORITHM: str

    model_config = _base_config


class NotificationSettings(BaseSettings):
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = False
    SUPPRESS_SEND: int = 0

    TWILIO_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_NUMBER: str

    model_config = _base_config


app_settings = AppSettings()
db_settings = DatabaseSettings()
security_settings = SecuritySettings()
notification_settings = NotificationSettings()

settings = db_settings