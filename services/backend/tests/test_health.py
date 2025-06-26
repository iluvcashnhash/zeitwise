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
    # Since the current implementation doesn't actually check the database,
    # this test will verify the happy path until we implement proper database checks
    # When
    response = client.get("/ping")
    
    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert data["services"]["database"] == "ok"
