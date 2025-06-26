"""
Authentication service for handling Supabase authentication.
"""
from typing import Optional, Dict, Any

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client as SupabaseClient

from app.core.config import settings

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class TokenData(BaseModel):
    """Token data model."""
    sub: str
    email: Optional[str] = None

class AuthService:
    """Service for handling authentication with Supabase."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.supabase: SupabaseClient = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
    
    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
        """Get current user from JWT token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            # Verify and decode the JWT token
            payload = jwt.decode(
                token,
                algorithms=["HS256"],  # Supabase uses HS256 by default
                options={"verify_aud": False},  # Disable audience verification for now
            )
            
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
                
            # Get user from Supabase
            response = self.supabase.auth.admin.get_user_by_id(user_id)
            if not response.user:
                raise credentials_exception
                
            return {
                "id": response.user.id,
                "email": response.user.email,
                "user_metadata": response.user.user_metadata or {},
                "app_metadata": response.user.app_metadata or {}
            }
            
        except JWTError as exc:
            raise credentials_exception from exc
    
    async def sign_in_with_email_password(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in with email and password."""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "user_metadata": response.user.user_metadata or {},
                    "app_metadata": response.user.app_metadata or {}
                }
            }
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            ) from exc
    
    async def sign_up_with_email_password(self, email: str, password: str, user_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Sign up with email and password."""
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata or {}
                }
            })
            
            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create user"
                )
                
            return {
                "id": response.user.id,
                "email": response.user.email,
                "email_confirmed": not response.user.email_confirmed_at is None,
                "user_metadata": response.user.user_metadata or {}
            }
            
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc)
            ) from exc
    
    async def sign_in_with_oauth(self, provider: str, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Sign in with OAuth provider."""
        try:
            response = self.supabase.auth.sign_in_with_oauth({
                "provider": provider,
                "options": {
                    "redirect_to": redirect_uri,
                    "query_params": {
                        "code": code
                    }
                }
            })
            
            if not response.url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to authenticate with {provider}"
                )
                
            # In a real implementation, you would handle the OAuth flow properly
            # This is a simplified version
            return {"message": "OAuth flow initiated", "url": response.url}
            
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc)
            ) from exc
    
    async def sign_in_with_phone_otp(self, phone: str) -> Dict[str, Any]:
        """Initiate phone OTP sign-in."""
        try:
            response = self.supabase.auth.sign_in_with_otp({"phone": phone})
            return {"message": "OTP sent successfully"}
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc)
            ) from exc
    
    async def verify_phone_otp(self, phone: str, token: str) -> Dict[str, Any]:
        """Verify phone OTP and sign in."""
        try:
            response = self.supabase.auth.verify_otp({
                "phone": phone,
                "token": token,
                "type": "sms"
            })
            
            if not response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid OTP"
                )
                
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": {
                    "id": response.user.id,
                    "phone": response.user.phone,
                    "user_metadata": response.user.user_metadata or {},
                    "app_metadata": response.user.app_metadata or {}
                }
            }
            
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc)
            ) from exc

# Create a singleton instance of the auth service
auth_service = AuthService()
