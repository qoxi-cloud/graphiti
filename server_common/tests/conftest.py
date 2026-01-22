"""Pytest configuration and fixtures for server_common tests."""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_yaml_file(temp_dir):
    """Create a temporary YAML config file."""

    def _create_yaml(content: str, filename: str = 'config.yaml') -> Path:
        path = temp_dir / filename
        path.write_text(content)
        return path

    return _create_yaml


@pytest.fixture
def clean_env():
    """Fixture to clean environment variables after test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_env(clean_env):
    """Fixture to set environment variables for testing."""

    def _set_env(**kwargs):
        for key, value in kwargs.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    return _set_env
