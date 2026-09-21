from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment and .env."""

    # --- Application ---
    APP_ENV: str = "development"
    APP_NAME: str = "Sentinel"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    # --- Backend ---
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_CORS_ORIGINS: str | list[str] = ["http://localhost:3000"]

    @property
    def cors_origins(self) -> list[str]:
        """Return CORS origins as a list of strings."""
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            return [
                origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()
            ]
        return list(self.BACKEND_CORS_ORIGINS)

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://sentinel:sentinel@localhost:5433/sentinel"
    DATABASE_URL_SYNC: str = "postgresql+psycopg://sentinel:sentinel@localhost:5433/sentinel"
    POSTGRES_USER: str = "sentinel"
    POSTGRES_PASSWORD: str = "sentinel"
    POSTGRES_DB: str = "sentinel"

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6381/0"
    REDIS_STREAM_EVENTS: str = "sentinel:events"
    REDIS_STREAM_ALERTS: str = "sentinel:alerts"

    # --- Auth / JWT ---
    JWT_SECRET: str = "change-me-in-production-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Sécurité ---
    RATE_LIMIT_PER_MINUTE: int = 120
    MAX_PAYLOAD_SIZE_BYTES: int = 1048576
    PASSWORD_HASH_ALGORITHM: str = "argon2"

    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
