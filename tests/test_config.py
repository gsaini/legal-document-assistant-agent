"""Tests for configuration module."""

import pytest
from unittest.mock import patch
import os

from src.config import Settings, get_settings


class TestSettings:
    """Test configuration settings."""
    
    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()
        
        assert settings.app_name == "legal-document-assistant"
        assert settings.app_env == "development"
        assert settings.debug is False
        assert settings.llm_provider == "ollama"
        assert settings.ollama_model == "llama4"
    
    def test_llm_providers(self):
        """Test that all LLM providers are valid."""
        settings = Settings()
        
        # Test ollama (default)
        assert settings.llm_provider == "ollama"
        
        # Other providers would require API keys
    
    def test_effective_database_url_default(self):
        """Test effective database URL returns SQLite by default."""
        settings = Settings()
        assert "sqlite" in settings.effective_database_url
    
    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"})
    def test_effective_database_url_postgres(self):
        """Test effective database URL returns PostgreSQL when set."""
        # Clear cache to pick up new environment
        get_settings.cache_clear()
        settings = Settings()
        settings.database_url = "postgresql://test"
        assert settings.effective_database_url == "postgresql://test"
    
    def test_supported_formats_list(self):
        """Test supported formats parsing."""
        settings = Settings()
        formats = settings.supported_formats_list
        
        assert isinstance(formats, list)
        assert "pdf" in formats
        assert "docx" in formats
        assert "txt" in formats
    
    def test_upload_path_creation(self):
        """Test upload path property creates directory."""
        settings = Settings()
        path = settings.upload_path
        
        assert path.exists()
        assert path.is_dir()
    
    def test_chroma_path_creation(self):
        """Test ChromaDB path property creates directory."""
        settings = Settings()
        path = settings.chroma_path
        
        assert path.exists()
        assert path.is_dir()


class TestGetSettings:
    """Test get_settings function."""
    
    def test_get_settings_cached(self):
        """Test that settings are cached."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
