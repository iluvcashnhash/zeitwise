from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import json
import httpx
from typing import Dict, Any, Optional

from app.core.config import settings

# Security scheme for JWT tokens
security = HTTPBearer(
    bearerFormat="JWT",
    description="Enter JWT Bearer token from Supabase Auth"
)

# Cache for JWKS
jwks_cache = {}

# Token validation settings
TOKEN_ALGORITHMS = ["HS256", "RS256"]
TOKEN_AUDIENCE = "authenticated"
TOKEN_ISSUER = f"{settings.SUPABASE_URL}/auth/v1" if settings.SUPABASE_URL else None

async def get_jwks() -> Dict[str, Any]:
    """Fetch JWKS from Supabase."""
    if not settings.SUPABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_URL is not configured"
        )
    
    jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch JWKS: {e.response.status_code} {e.response.reason_phrase}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Auth service unavailable: {str(e)}"
        )

async def get_public_key(kid: str) -> str:
    """Get public key for a given key ID from JWKS."""
    if not jwks_cache:
        jwks = await get_jwks()
        jwks_cache.update({key['kid']: key for key in jwks.get('keys', [])})
    
    key = jwks_cache.get(kid)
    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: unknown key ID"
        )
    
    return key

def get_token_issuer() -> str:
    """Get the token issuer URL based on Supabase URL."""
    if not settings.SUPABASE_URL:
        raise ValueError("SUPABASE_URL is not configured")
    return f"{settings.SUPABASE_URL}/auth/v1"


def verify_token_claims(payload: Dict[str, Any]) -> None:
    """Verify standard JWT claims."""
    now = datetime.now(timezone.utc)
    
    # Check token expiration
    if "exp" in payload and datetime.fromtimestamp(payload["exp"], tz=timezone.utc) < now:
        raise JWTError("Token has expired")
        
    # Check not before time
    if "nbf" in payload and datetime.fromtimestamp(payload["nbf"], tz=timezone.utc) > now:
        raise JWTError("Token not yet valid")
    
    # Check audience
    if "aud" in payload and payload["aud"] != TOKEN_AUDIENCE:
        raise JWTError(f"Invalid audience: {payload['aud']}")
    
    # Check issuer if configured
    if TOKEN_ISSUER and "iss" in payload and payload["iss"] != TOKEN_ISSUER:
        raise JWTError(f"Invalid issuer: {payload['iss']}")


async def decode_jwt(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication token provided"
        )
        
    try:
        # Get the JWT header to find the key ID
        header = jwt.get_unverified_header(token)
        header = jwt.get_unverified_header(token)
        kid = header.get('kid')
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing key ID"
            )
        
        # Get the public key
        public_key = await get_public_key(kid)
        
        # Decode the token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[public_key['alg']],
            audience='authenticated',
            issuer=settings.SUPABASE_URL + '/auth/v1',
            options={"verify_aud": True, "verify_iss": True}
        )
        
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to get the current user from the Supabase JWT token.
    
    Args:
        request: The incoming request object
        credentials: The HTTP Authorization credentials containing the JWT
        
    Returns:
        Dict containing the decoded JWT payload with user information
        
    Raises:
        HTTPException: If the token is invalid or user is not authenticated
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    try:
        # Decode and verify the JWT token
        payload = await decode_jwt(credentials.credentials)
        
        # Verify standard JWT claims
        verify_token_claims(payload)
        
        # Extract user information
        user_info = {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "email_verified": payload.get("email_verified", False),
            "phone_verified": payload.get("phone_verified", False),
            "app_metadata": payload.get("app_metadata", {}),
            "user_metadata": payload.get("user_metadata", {})
        }
        
        # Store user info in request state for use in route handlers
        request.state.user = user_info
        
        return user_info
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # Log the error for debugging
        request.app.logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during authentication"
        )


def get_required_roles(*roles: str):
    """
    Dependency factory to require specific roles for an endpoint.
    
    Example usage:
        @router.get("/admin", dependencies=[Depends(get_required_roles("admin", "moderator"))])
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_roles = current_user.get("app_metadata", {}).get("roles", [])
        if not any(role in user_roles for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
        
    return role_checker
