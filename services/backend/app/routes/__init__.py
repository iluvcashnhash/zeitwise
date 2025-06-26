# This file makes the routes directory a Python package

from fastapi import APIRouter
from . import chat, detox, integrations

# Create a main router to include all other routers
api_router = APIRouter()

# Include all routers
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(detox.router, prefix="/detox", tags=["detox"])
api_router.include_router(integrations.router, prefix="", tags=["integrations"])

# Make all routers available for direct import
__all__ = ["api_router", "chat", "detox", "integrations"]
