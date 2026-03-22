"""Configuration management using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Tushare (required)
    tushare_token: str = ""

    # Claude / Anthropic API
    anthropic_api_key: str = ""
    anthropic_base_url: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Analysis
    max_history_days: int = 365
    default_market: str = "cn"

    # Agent
    max_iterations: int = 10
    temperature: float = 0.7

    # Neo4j / Graphiti
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    graphiti_database: str = "quant_research"

    # SQLite / Vector Store
    sqlite_db_path: str = "data/quant.db"

    # Embedding
    embedding_api_key: str = ""
    embedding_base_url: str = ""
    embedding_model: str = ""
    embedding_dimension: int = 0

    # Graphiti LLM (OpenAI-compatible API)
    graphiti_llm_model: str = ""
    graphiti_llm_base_url: str = ""
    graphiti_llm_api_key: str = ""
    openai_api_key: str = ""
    openai_base_url: str = ""


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
