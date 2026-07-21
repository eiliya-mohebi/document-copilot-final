from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    supabase_url: str = Field(min_length=1)
    supabase_anon_key: str = Field(min_length=1)
    supabase_service_role_key: str = Field(min_length=1)

    # Direct/session Postgres URL (not the transaction pooler).
    database_url: str = Field(min_length=1)

    # Comma-separated in .env; use `cors_origins` for the parsed list.
    allowed_origins: str = "http://localhost:5173"

    # OpenAI-compatible API (AvalAI). Key is only required by ingest/LLM paths,
    # which validate it at their own entry points so the API can boot without it.
    openai_api_key: str = ""
    openai_base_url: str = "https://api.avalai.ir/v1"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]

    @computed_field
    @property
    def async_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgresql+psycopg://"):
            return url
        if url.startswith("postgresql://"):
            return "postgresql+psycopg://" + url.removeprefix("postgresql://")
        if url.startswith("postgres://"):
            return "postgresql+psycopg://" + url.removeprefix("postgres://")
        raise ValueError(
            "DATABASE_URL must be a postgres URL "
            "(postgresql://, postgres://, or postgresql+psycopg://)"
        )


settings = Settings()
