"""Meme generation routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user_model import User
from app.api.endpoints import memes as meme_endpoints

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Include meme endpoints
router.include_router(
    meme_endpoints.router,
    prefix="/memes",
    tags=["Memes"]
)

# Log all registered meme routes
for route in router.routes:
    logger.info(f"Registered meme route: {route.path} - {', '.join(route.methods)}")

# Make router available for direct import
__all__ = ["router"]
