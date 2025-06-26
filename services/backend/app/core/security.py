from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from jose.utils import base64url_decode
import json
import httpx
from typing import Optional, Dict, Any

from app.core.config import settings

# Security scheme for JWT tokens
security = HTTPBearer()

# Cache for JWKS
jwks_cache = {}

async def get_jwks() -> Dict[str, Any]:
    """Fetch JWKS from Supabase."""
    jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch JWKS: {str(e)}"
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

async def decode_jwt(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token."""
    try:
        # Get the JWT header to find the key ID
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

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Dependency to get the current user from the JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    try:
        payload = await decode_jwt(token)
        return {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "app_metadata": payload.get("app_metadata", {}),
            "user_metadata": payload.get("user_metadata", {})
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
