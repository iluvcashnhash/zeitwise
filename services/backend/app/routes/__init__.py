# This file makes the routes directory a Python package
import logging
from fastapi import APIRouter

# Set up logging
logger = logging.getLogger(__name__)

# Create a main router to include all other routers
api_router = APIRouter()

try:
    # Import and include all routers
    logger.info("Importing chat router...")
    from . import chat
    logger.info("Importing detox router...")
    from . import detox
    logger.info("Importing integrations router...")
    from . import integrations
    
    # Include all routers with their prefixes
    logger.info("Including chat router at /chat")
    api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
    logger.info("Including detox router at /detox")
    api_router.include_router(detox.router, prefix="/detox", tags=["detox"])
    logger.info("Including integrations router at /")
    api_router.include_router(integrations.router, prefix="", tags=["integrations"])
    
    # Log all registered routes
    for route in api_router.routes:
        logger.info(f"Registered route: {route.path} - {', '.join(route.methods)}")
    
except Exception as e:
    logger.error(f"Error setting up routes: {e}", exc_info=True)
    raise

# Make all routers available for direct import
__all__ = ["api_router", "chat", "detox", "integrations"]
