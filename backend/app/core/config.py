from typing import List, Union
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "بينة AI (Bayyinah Engine)"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Database connection parameters
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "bayyinah_user"
    POSTGRES_PASSWORD: str = "bayyinah_secure_pass"
    POSTGRES_DB: str = "bayyinah_db"

    # Vector embedding configuration
    EMBEDDING_DIMENSION: int = 1536

    # CORS origins
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
