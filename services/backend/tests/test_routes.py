"""Test route registration and availability."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import api_router

@pytest.fixture
def test_app():
    """Create a test FastAPI app with all routes."""
    app = FastAPI()
    app.include_router(api_router, prefix="/api")
    return app

def test_list_routes(test_app):
    """List all registered routes for debugging."""
    routes = []
    for route in test_app.routes:
        methods = ", ".join(route.methods) if hasattr(route, "methods") else ""
        routes.append(f"{route.path} - {methods}")
    
    # Print all routes for debugging
    print("\nRegistered routes:")
    for route in sorted(routes):
        print(f"- {route}")
    
    # Basic assertion to ensure the test runs
    assert len(routes) > 0, "No routes registered"
