from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, List, Optional

from app.core.config import settings

# Create main API router
api_router = APIRouter()

# Import and include other routers here
# from .endpoints import users, auth, items, etc.

# Health check endpoint
@api_router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for the API."""
    return {"status": "ok"}

# Example router for future endpoints
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Example endpoint
@api_router.get("/version", tags=["info"])
async def get_version() -> dict[str, str]:
    """Get the current API version."""
    return {"version": settings.VERSION}
