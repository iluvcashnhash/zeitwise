import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, MagicMock
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.core.config import settings
from app.core.security import get_current_user

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
def client():
    """Test client fixture."""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_jwt():
    """Mock JWT token in the request header."""
    return {"Authorization": f"Bearer {MOCK_JWT_TOKEN}"}

@pytest.fixture
def mock_auth():
    """Mock authentication."""
    async def mock_get_current_user():
        return MOCK_USER
    
    with patch("app.routes.chat.get_current_user", mock_get_current_user), \
         patch("app.routes.detox.get_current_user", mock_get_current_user), \
         patch("app.routes.integrations.get_current_user", mock_get_current_user):
        yield

@pytest.fixture
authenticated_client(client, mock_auth, mock_jwt):
    """Test client with authentication."""
    client.headers.update(mock_jwt)
    return client

# Mock environment variables for tests
@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Mock environment variables."""
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("SUPABASE_URL", "http://mock-supabase:54321")
    monkeypatch.setenv("SUPABASE_KEY", "mock-supabase-key")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
