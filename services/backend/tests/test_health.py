"""Tests for health check endpoints."""
import pytest
from fastapi import status
from unittest.mock import patch

# Test the /ping endpoint
def test_ping_endpoint(client):
    """Test the /ping endpoint returns expected response."""
    # When
    response = client.get("/ping")
    
    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert "services" in data
    assert "database" in data["services"]
    assert "version" in data

# Test the /healthz endpoint
def test_healthz_endpoint(client):
    """Test the /healthz endpoint returns expected response."""
    # When
    response = client.get("/healthz")
    
    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data == {"status": "ok"}

# Test database health check failure
@patch("app.main.HealthStatus")
def test_database_health_check_failure(mock_health_status, client):
    """Test database health check failure."""
    # Given
    from app.schemas.responses import HealthStatus
    mock_health_status.ERROR = "error"
    
    # Mock database check to fail
    with patch("app.main.HealthCheckResponse") as mock_response:
        mock_response.return_value.services = {"database": "error"}
        mock_response.return_value.status = "error"
        
        # When
        response = client.get("/ping")
    
    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "error"
    assert data["services"]["database"] == "error"
