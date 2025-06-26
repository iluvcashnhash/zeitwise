import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, status, Depends
from fastapi.security import HTTPBearer
from unittest.mock import patch, MagicMock
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app as main_app
from app.core.config import settings
from app.core.security import get_current_user, security

@pytest.fixture(scope="module")
def app():
    """Create a test FastAPI application."""
    # Create a new FastAPI app for testing
    test_app = FastAPI()
    
    # Include all routers from the main app
    test_app.include_router(main_app.router)
    
    # Apply any test-specific middleware or overrides
    return test_app

# Mock user data for testing
MOCK_USER = {
    "sub": "auth0|1234567890",
    "email": "test@example.com",
    "role": "user",
    "app_metadata": {},
    "user_metadata": {}
}

# Mock JWT token for testing
MOCK_JWT_TOKEN = "mock.jwt.token"

@pytest.fixture(scope="module")
def client(app):
    """Test client fixture."""
    # Create a test client using the test app
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_jwt():
    """Mock JWT token in the request header."""
    return {"Authorization": f"Bearer {MOCK_JWT_TOKEN}"}

@pytest.fixture(autouse=True)
def override_dependencies(app):
    """Override dependencies for testing."""
    # Create a mock security scheme that always returns a valid token
    async def mock_get_current_user():
        return MOCK_USER
    
    # Mock the security dependency to always return a valid token
    async def mock_security():
        return {"credentials": "mock-token"}
    
    # Override the dependencies
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[security] = mock_security
    
    yield
    
    # Clean up after tests
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def mock_auth():
    """Mock authentication for all tests."""
    # This is now handled by override_dependencies
    yield

@pytest.fixture
def authenticated_client(client):
    """Test client with authentication."""
    # Ensure the client has a valid token in the header
    client.headers.update({
        "Authorization": f"Bearer {MOCK_JWT_TOKEN}",
        "Content-Type": "application/json"
    })
    return client

# Mock environment variables for tests
@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Mock environment variables."""
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("SUPABASE_URL", "http://mock-supabase:54321")
    monkeypatch.setenv("SUPABASE_KEY", "mock-supabase-key")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
