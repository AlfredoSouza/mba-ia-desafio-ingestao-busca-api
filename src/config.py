from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/ragdb",
        alias="DATABASE_URL",
    )
    collection_name: str = Field(default="pdf_documents", alias="COLLECTION_NAME")
    embedding_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL")
    chat_model: str = Field(default="gpt-5-nano", alias="OPENAI_CHAT_MODEL")
    upload_dir: Path = Field(default=Path("uploads"), alias="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=20, alias="MAX_UPLOAD_SIZE_MB")
    api_url: str = Field(default="http://localhost:8000", alias="API_URL")

    @property
    def psycopg_url(self) -> str:
        return self.database_url.replace("postgresql+psycopg://", "postgresql://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
