from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    APP_NAME: str = "academic-api"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: str
    # SQLAlchemy precisa de driver diferente para async
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://").replace(
            "postgres://", "postgresql+asyncpg://"
        )

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 15
    JWT_REFRESH_EXPIRES_DAYS: int = 7

    LOG_LEVEL: str = "info"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
