"""
Pytest configuration and fixtures for FastAPI tests.
Provides isolated app instances and TestClient for each test.
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app as fastapi_app


@pytest.fixture
def app():
    """
    Fixture that provides a fresh FastAPI app instance with isolated state.
    Each test gets its own copy of the activities dictionary.
    """
    # Import the app module to get a fresh instance
    import importlib
    import app as app_module
    importlib.reload(app_module)
    return app_module.app


@pytest.fixture
def client(app):
    """
    Fixture that provides a TestClient instance for the FastAPI app.
    Uses the app fixture to ensure isolation between tests.
    """
    return TestClient(app)
