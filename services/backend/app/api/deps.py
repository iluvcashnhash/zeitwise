"""Dependencies for FastAPI endpoints."""
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.deps import get_db
from app.models.user_model import User
from app.services.user_sync import UserSyncService, get_user_sync_service

# Reusable HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)

async def get_current_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """
    Get the current user ID from the JWT token in the Authorization header.
    
    This is a low-level function that only validates the JWT and extracts the user ID.
    It does not check if the user exists in the database.
    
    Args:
        request: The FastAPI request object
        credentials: The HTTP Authorization header
        
    Returns:
        The user ID from the JWT token, or None if no valid token was found
        
    Raises:
        HTTPException: If the token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try to get token from Authorization header
    token = None
    if credentials is not None:
        token = credentials.credentials
    else:
        # Try to get token from cookies
        token = request.cookies.get(settings.SUPABASE_AUTH_COOKIE_NAME)
    
    if not token:
        return None
    
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[ALGORITHM],
            audience="authenticated",
            options={"verify_aud": True},
        )
        
        # Get user ID from token
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        return user_id
        
    except (JWTError, ValidationError) as exc:
        # Log the error but don't fail yet - we'll handle this in get_current_user
        return None

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_sync: UserSyncService = Depends(get_user_sync_service),
) -> User:
    """
    Get the current authenticated user.
    
    This dependency will:
    1. Extract and validate the JWT token from the request
    2. Get the user ID from the token
    3. Sync the user from Supabase Auth to the local database
    4. Return the user object
    
    Args:
        request: The FastAPI request object
        db: The database session
        user_sync: The user sync service
        
    Returns:
        The authenticated user
        
    Raises:
        HTTPException: If the user is not authenticated or an error occurs
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Get the current user ID from the JWT token
    user_id = await get_current_user_id(request)
    if not user_id:
        raise credentials_exception
    
    try:
        # Sync the user from Supabase Auth to the local database
        user = await user_sync.sync_user_from_supabase(user_id)
        if not user:
            raise credentials_exception
            
        return user
        
    except Exception as exc:
        # Log the error and return 401
        raise credentials_exception

# Dependency to get the current active user (must be authenticated and active)
async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active user.
    
    This dependency requires that the user is authenticated and active.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Dependency to get the current superuser (must be authenticated, active, and a superuser)
async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get the current superuser.
    
    This dependency requires that the user is authenticated, active, and a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user
