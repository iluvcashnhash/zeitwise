import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.schemas.requests import IntegrationRequest, IntegrationConfig, IntegrationType
from app.schemas.responses import IntegrationResponse, IntegrationStatus

# Test client is provided by the client fixture in conftest.py

def test_list_integration_types(authenticated_client):
    """Test listing all available integration types."""
    response = authenticated_client.get("/api/integrations/types")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0
    assert all("type" in item for item in response.json())
    assert all("name" in item for item in response.json())
    assert all("description" in item for item in response.json())
    assert all("settings_schema" in item for item in response.json())

@pytest.mark.asyncio
async def test_create_integration(authenticated_client, mock_auth):
    """Test creating a new integration."""
    response = authenticated_client.post(
        "/api/integrations",
        json={
            "action": "create",
            "config": {
                "type": "telegram",
                "settings": {"api_token": "test-token"},
                "enabled": True
            }
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["type"] == "telegram"
    assert data["settings"]["api_token"] == "test-token"
    assert data["enabled"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    # The user_id should be set by the mock_auth fixture
    assert data["user_id"] == "auth0|1234567890"

@pytest.mark.asyncio
async def test_create_integration_missing_config(authenticated_client, mock_auth):
    """Test creating an integration with missing config."""
    response = authenticated_client.post(
        "/api/integrations",
        json={"action": "create"}  # Missing config
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "config" in data["detail"][0]["loc"]
    assert "field required" in data["detail"][0]["msg"].lower()

@pytest.fixture
def test_integration_data():
    """Fixture providing test integration data."""
    from app.schemas.responses import IntegrationStatus
    
    return {
        "test-integration-123": {
            "id": "test-integration-123",
            "user_id": "auth0|1234567890",  # Matches mock_auth user
            "type": "telegram",
            "settings": {"api_token": "test-token"},
            "enabled": False,
            "status": IntegrationStatus.ACTIVE,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        },
        "test-integration-456": {
            "id": "test-integration-456",
            "user_id": "auth0|1234567890",
            "type": "rss",
            "settings": {"feed_url": "http://example.com/feed"},
            "enabled": False,
            "status": IntegrationStatus.ACTIVE,
            "created_at": "2023-01-02T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z"
        }
    }

@pytest.mark.asyncio
async def test_update_integration(authenticated_client, mock_auth, test_integration_data):
    """Test updating an existing integration."""
    test_integration_id = "test-integration-123"
    
    with patch("app.routes.integrations.integrations_db", test_integration_data), \
         patch("app.routes.integrations.datetime") as mock_datetime:
        
        # Mock the current time
        mock_now = "2023-01-02T00:00:00Z"
        mock_datetime.now.return_value = mock_now
        
        # Update the integration
        response = authenticated_client.post(
            "/api/integrations",
            json={
                "action": "update",
                "integration_id": test_integration_id,
                "config": {
                    "enabled": True,
                    "settings": {"api_token": "new-token"}
                }
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_integration_id
        assert data["enabled"] is True
        assert data["settings"]["api_token"] == "new-token"
        assert data["updated_at"] == mock_now  # Should be updated
        assert data["created_at"] == "2023-01-01T00:00:00Z"  # Should remain unchanged

@pytest.mark.asyncio
async def test_delete_integration(authenticated_client, mock_auth, test_integration_data):
    """Test deleting an integration."""
    test_integration_id = "test-integration-123"
    
    with patch("app.routes.integrations.integrations_db", test_integration_data):
        
        # Delete the integration
        response = authenticated_client.post(
            "/api/integrations",
            json={
                "action": "delete",
                "integration_id": test_integration_id
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert test_integration_id not in test_integration_data

@pytest.mark.asyncio
async def test_sync_integration(authenticated_client, mock_auth, test_integration_data):
    """Test syncing an integration."""
    test_integration_id = "test-integration-123"
    
    with patch("app.routes.integrations.integrations_db", test_integration_data), \
         patch("app.routes.integrations.datetime") as mock_datetime:
        
        # Mock the current time
        mock_now = "2023-01-02T00:00:00Z"
        mock_datetime.now.return_value = mock_now
        
        # Trigger sync
        response = authenticated_client.post(
            "/api/integrations",
            json={
                "action": "sync",
                "integration_id": test_integration_id
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["last_synced"] == mock_now
        assert data["updated_at"] == mock_now

@pytest.mark.asyncio
async def test_list_integrations(authenticated_client, mock_auth, test_integration_data):
    """Test listing integrations with filters."""
    with patch("app.routes.integrations.integrations_db", test_integration_data):
        # List all integrations
        response = authenticated_client.get("/api/integrations")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2  # Should return both test integrations
        
        # Filter by type
        response = authenticated_client.get("/api/integrations?type=telegram")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["type"] == "telegram"
        
        # Filter by enabled
        response = authenticated_client.get("/api/integrations?enabled=false")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2  # Both test integrations have enabled=False
        
        # Filter by both type and enabled
        response = authenticated_client.get("/api/integrations?type=telegram&enabled=false")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["type"] == "telegram"
        assert data[0]["enabled"] is False
