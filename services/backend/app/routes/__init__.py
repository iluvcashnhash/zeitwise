# This file makes the routes directory a Python package
import logging
from fastapi import APIRouter

# Set up logging
logger = logging.getLogger(__name__)

# Create a main router to include all other routers
api_router = APIRouter()

try:
    # Import and include all routers
    logger.info("Importing auth router...")
    from . import auth
    logger.info("Importing chat router...")
    from . import chat
    logger.info("Importing detox router...")
    from . import detox
    logger.info("Importing integrations router...")
    from . import integrations
    logger.info("Importing verification router...")
    from . import verification
    logger.info("Importing memes router...")
    from . import memes
    
    # Include all routers with their prefixes
    logger.info("Including auth router at /auth")
    api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    logger.info("Including verification router at /verification")
    api_router.include_router(verification.router, prefix="/verification", tags=["Verification"])
    logger.info("Including memes router at /memes")
    api_router.include_router(memes.router, prefix="/memes", tags=["Memes"])
    logger.info("Including chat router at /chat")
    api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
    logger.info("Including detox router at /detox")
    api_router.include_router(detox.router, prefix="/detox", tags=["Detox"])
    logger.info("Including integrations router at /")
    api_router.include_router(integrations.router, prefix="", tags=["Integrations"])
    
    # Log all registered routes
    for route in api_router.routes:
        logger.info(f"Registered route: {route.path} - {', '.join(route.methods)}")
    
except Exception as e:
    logger.error(f"Error setting up routes: {e}", exc_info=True)
    raise

# Make all routers available for direct import
__all__ = ["api_router", "auth", "verification", "memes", "chat", "detox", "integrations"]
