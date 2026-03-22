"""Pytest configuration."""

import pytest


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")
    monkeypatch.setenv("TUSHARE_TOKEN", "test_token")
