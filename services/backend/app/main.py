from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any
import logging
import os
import time

from .core.config import settings
from .core.security import get_current_user
from .schemas.responses import HealthCheckResponse, HealthStatus

# Import routers
from .routes import chat, detox, integrations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for FastAPI app."""
    # Startup
    logger.info("Starting up...")
    
    # Initialize resources (database connections, etc.)
    # await database.connect()
    
    # Initialize services
    await initialize_services()
    
    yield  # The application runs here
    
    # Shutdown
    logger.info("Shutting down...")
    # await database.disconnect()

async def initialize_services() -> None:
    """Initialize application services."""
    # TODO: Initialize database connections, caches, etc.
    pass

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for ZeitWise application",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(detox.router, prefix="/api/v1/detox", tags=["detox"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"])

# Health check endpoint
@app.get("/ping", response_model=HealthCheckResponse, tags=["health"])
async def ping() -> HealthCheckResponse:
    """Health check endpoint."""
    status = HealthStatus.OK
    services: Dict[str, HealthStatus] = {
        "database": HealthStatus.OK,  # TODO: Check database connection
        # Add other service checks as needed
    }
    
    # If any service is down, mark overall status as ERROR
    if any(status == HealthStatus.ERROR for status in services.values()):
        status = HealthStatus.ERROR
    
    return HealthCheckResponse(
        status=status,
        services=services,
    )

# Simple health check for load balancers
@app.get("/healthz", include_in_schema=False)
async def healthz() -> Dict[str, str]:
    """Health check endpoint for load balancers."""
    return {"status": "ok"}

# Custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Root endpoint - redirect to docs
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.PROJECT_NAME,
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "environment": settings.ENVIRONMENT,
    }
