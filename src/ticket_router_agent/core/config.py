from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="AI Powered Intelligent Ticket Routing & Resolution Agent")
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO")
    api_prefix: str = Field(default="/api/v1")
    database_url: str = Field(default="sqlite:///./data/tickets.db")
    seed_data_path: Path = Field(default=Path("./data/seed_tickets.json"))
    embedding_provider: str = Field(default="sentence_transformers")
    sentence_transformers_model: str = Field(default="all-MiniLM-L6-v2")
    openai_api_key: str = Field(default="")
    openai_embedding_model: str = Field(default="text-embedding-3-small")
    faiss_index_path: Path = Field(default=Path("./data/faiss.index"))
    faiss_metadata_path: Path = Field(default=Path("./data/faiss_metadata.json"))
    escalation_threshold: float = Field(default=0.60)
    repeat_issue_window_days: int = Field(default=30)
    repeat_issue_min_count: int = Field(default=3)
    default_top_k: int = Field(default=5)

    @property
    def sqlite_path(self) -> Path:
        if self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.replace("sqlite:///", "", 1))
        return Path("./data/tickets.db")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
