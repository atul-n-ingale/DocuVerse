"""
Unit tests for app.core.config module.
"""

import os
from unittest.mock import patch

import pytest  # type: ignore

from app.core.config import Settings, settings


@pytest.mark.unit
class TestSettings:
    """Test cases for Settings class."""

    @patch.dict(os.environ, {}, clear=True)
    def test_settings_creation(self):
        """Test that Settings can be created with default values."""
        test_settings = Settings()
        # The MongoDB URI might be localhost or mongodb depending on environment
        assert test_settings.mongodb_uri in ["mongodb://localhost:27017/docuverse", "mongodb://mongodb:27017/docuverse"]
        # The Redis URL might be localhost or redis depending on environment
        assert test_settings.redis_url in ["redis://localhost:6379/0", "redis://redis:6379/0"]
        assert test_settings.backend_url == "http://localhost:8000"
        assert test_settings.upload_dir == "uploads"
        assert test_settings.max_file_size == 50 * 1024 * 1024

    def test_settings_with_custom_values(self):
        """Test that Settings can be created with custom values."""
        test_settings = Settings(
            mongodb_uri="mongodb://test:27017/test_db",
            redis_url="redis://test:6379/0",
            openai_api_key="test-key",
            pinecone_api_key="test-key",
            pinecone_environment="test-env",
        )
        assert test_settings.mongodb_uri == "mongodb://test:27017/test_db"
        assert test_settings.redis_url == "redis://test:6379/0"
        assert test_settings.openai_api_key == "test-key"
        assert test_settings.pinecone_api_key == "test-key"
        assert test_settings.pinecone_environment == "test-env"

    def test_supported_extensions(self):
        """Test that supported extensions are properly configured."""
        test_settings = Settings()
        expected_extensions = [".pdf", ".docx", ".csv", ".xlsx", ".xls", ".png", ".jpg", ".jpeg"]
        assert test_settings.supported_extensions == expected_extensions

    @patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": "env-openai-key",
            "PINECONE_API_KEY": "env-pinecone-key",
            "PINECONE_ENVIRONMENT": "env-pinecone-env",
        },
        clear=True,
    )
    def test_settings_from_environment(self):
        """Test that Settings can read from environment variables."""
        test_settings = Settings()
        assert test_settings.openai_api_key == "env-openai-key"
        assert test_settings.pinecone_api_key == "env-pinecone-key"
        assert test_settings.pinecone_environment == "env-pinecone-env"

    def test_global_settings_instance(self):
        """Test that global settings instance is properly configured."""
        assert isinstance(settings, Settings)
        assert hasattr(settings, "openai_api_key")
        assert hasattr(settings, "pinecone_api_key")
        assert hasattr(settings, "mongodb_uri")
