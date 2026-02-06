"""Legal Document Assistant - Configuration Module."""

from functools import lru_cache
from typing import Literal
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="legal-document-assistant")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development"
    )
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # API Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # LLM Configuration
    # Supports: "ollama" (open source), "openai", "anthropic"
    llm_provider: Literal["ollama", "openai", "anthropic"] = Field(default="ollama")
    
    # Ollama (open source, local)
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama4")
    
    # OpenAI (optional, for cloud deployments)
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default="gpt-4o")
    
    # Anthropic (optional)
    anthropic_api_key: str | None = Field(default=None)
    anthropic_model: str = Field(default="claude-3-sonnet-20240229")

    # Vector Store (ChromaDB - open source)
    chroma_persist_directory: str = Field(default="./data/chroma")
    chroma_contracts_collection: str = Field(default="contracts")
    chroma_case_law_collection: str = Field(default="case_law")
    chroma_clauses_collection: str = Field(default="approved_clauses")

    # Database
    # SQLite for development (open source)
    sqlite_database_url: str = Field(
        default="sqlite+aiosqlite:///./data/legal_docs.db"
    )
    # PostgreSQL for production (open source)
    database_url: str | None = Field(default=None)

    # OCR Configuration (Tesseract - open source)
    tesseract_cmd: str = Field(default="/usr/local/bin/tesseract")
    ocr_languages: str = Field(default="eng")

    # Document Processing
    upload_directory: str = Field(default="./data/uploads")
    max_file_size_mb: int = Field(default=50)
    supported_formats: str = Field(default="pdf,docx,doc,txt,png,jpg,jpeg")

    # Security & Compliance
    encryption_key: str | None = Field(default=None)
    pii_detection_enabled: bool = Field(default=True)
    audit_log_enabled: bool = Field(default=True)
    audit_log_path: str = Field(default="./data/audit/audit.log")

    # Redis (open source, optional)
    redis_url: str = Field(default="redis://localhost:6379/0")

    # spaCy NLP Model (open source)
    spacy_model: str = Field(default="en_core_web_lg")

    @property
    def effective_database_url(self) -> str:
        """Get the effective database URL (PostgreSQL if set, else SQLite)."""
        return self.database_url or self.sqlite_database_url

    @property
    def supported_formats_list(self) -> list[str]:
        """Get list of supported file formats."""
        return [fmt.strip().lower() for fmt in self.supported_formats.split(",")]

    @property
    def upload_path(self) -> Path:
        """Get the upload directory path."""
        path = Path(self.upload_directory)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def chroma_path(self) -> Path:
        """Get ChromaDB persistence path."""
        path = Path(self.chroma_persist_directory)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
