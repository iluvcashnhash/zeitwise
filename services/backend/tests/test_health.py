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
def test_database_health_check_failure(client):
    """Test database health check failure."""
    # Mock the database health check to fail
    with patch("app.main.check_database_health") as mock_db_check:
        # Configure the mock to return an error status
        mock_db_check.return_value = {
            "status": "error",
            "details": "Connection failed"
        }
        
        # When
        response = client.get("/ping")
    
    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "error"
    assert data["services"]["database"] == "error"
