"""
Supabase authentication service for handling JWT and user authentication.
"""
from typing import Dict, Optional, Any, Union
from datetime import datetime, timedelta
import logging

from fastapi import HTTPException, status, Depends, Request

from app.core.config import settings
from app.core.security import get_current_user
from app.services.supabase_client import get_supabase_client
from app.models.user import User, UserCreate, UserUpdate
from app.db.crud.users import get_user_by_id, create_user, update_user

logger = logging.getLogger(__name__)

class SupabaseAuthService:
    """Service for handling Supabase authentication and user management."""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.admin = get_supabase_admin_client()
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email from Supabase Auth."""
        try:
            result = self.admin.auth.admin.list_users()
            users = [u.model_dump() for u in result.users if u.email == email]
            return users[0] if users else None
        except Exception as e:
            logger.error(f"Error getting user by email from Supabase: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID from Supabase Auth."""
        try:
            result = self.admin.auth.admin.get_user_by_id(user_id)
            return result.user.model_dump() if hasattr(result, 'user') and result.user else None
        except Exception as e:
            logger.error(f"Error getting user by ID from Supabase: {e}")
            return None
    
    async def update_user(
        self, 
        user_id: str, 
        email: Optional[str] = None, 
        password: Optional[str] = None,
        user_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Update a user in Supabase Auth."""
        try:
            update_data = {}
            if email is not None:
                update_data["email"] = email
            if password is not None:
                update_data["password"] = password
            if user_metadata is not None:
                update_data["user_metadata"] = user_metadata
                
            update_data.update(kwargs)
            
            result = self.admin.auth.admin.update_user_by_id(user_id, **update_data)
            return result.user.model_dump() if hasattr(result, 'user') and result.user else {}
        except Exception as e:
            logger.error(f"Error updating user in Supabase: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update user: {str(e)}"
            )
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user from Supabase Auth."""
        try:
            self.admin.auth.admin.delete_user(user_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting user from Supabase: {e}")
            return False
    
    async def reset_password_for_email(self, email: str, redirect_to: Optional[str] = None) -> bool:
        """Send a password reset email to a user."""
        try:
            result = self.supabase.auth.reset_password_email(email, {"redirect_to": redirect_to or f"{settings.SUPABASE_URL}/auth/update-password"})
            return True
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
            # Don't reveal if the email exists or not
            return True
    
    async def verify_email(self, token: str) -> bool:
        """Verify a user's email using a verification token."""
        try:
            result = self.supabase.auth.verify_otp({"token_hash": token, "type": "signup"})
            return bool(result and hasattr(result, 'user') and result.user)
        except Exception as e:
            logger.error(f"Error verifying email: {e}")
            return False
    
    async def sign_in_with_email_password(
        self, 
        email: str, 
        password: str,
    ) -> Dict[str, Any]:
        """
        Sign in a user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dict containing user and session information
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            result = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })
            
            if not result or not hasattr(result, 'user') or not result.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                )
            
            # Add provider info to user metadata
            user_data = result.user.model_dump()
            user_metadata = user_data.get("user_metadata", {})
            user_metadata["provider"] = "email"
            user_metadata["providers"] = list(set(user_metadata.get("providers", []) + ["email"]))
            
            # Update user metadata if needed
            if "provider" not in user_data.get("user_metadata", {}) or "providers" not in user_data.get("user_metadata", {}):
                await self.update_user(
                    user_data["id"],
                    user_metadata=user_metadata
                )
            
            return {
                "user": user_data,
                "session": result.session.model_dump() if hasattr(result, 'session') else None,
                "provider": "email",
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error signing in with email/password: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
    
    async def sign_up_with_email_password(
        self, 
        email: str, 
        password: str,
        user_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Sign up a new user with email and password."""
        try:
            result = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata or {}
                }
            })
            return result.dict()
        except Exception as e:
            logger.error(f"Error signing up with email/password: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create user"
            )
    
    async def sign_in_with_oauth(
        self,
        provider: str,
        code: str = None,
        redirect_uri: str = None,
        auth_code: str = None,
    ) -> Dict[str, Any]:
        """
        Sign in or get OAuth URL for a provider.
        
        Args:
            provider: OAuth provider (google, github, etc.)
            code: Authorization code from OAuth provider (for token exchange)
            redirect_uri: Redirect URI for OAuth flow
            auth_code: Authentication code for token exchange (alternative to code)
            
        Returns:
            Dict containing OAuth URL or user session
            
        Raises:
            HTTPException: If OAuth flow fails
        """
        try:
            # Normalize provider name
            provider = provider.lower()
            
            # If we have a code, exchange it for a session
            if code or auth_code:
                result = self.supabase.auth.exchange_code_for_session(auth_code or code)
                
                if not result or not hasattr(result, 'user') or not result.user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to authenticate with {provider}",
                    )
                
                # Add provider info to user metadata
                user_data = result.user.model_dump()
                user_metadata = user_data.get("user_metadata", {})
                user_metadata["provider"] = provider
                
                # Track all providers for this user
                providers = set(user_metadata.get("providers", []))
                providers.add(provider)
                user_metadata["providers"] = list(providers)
                
                # Update user metadata if needed
                if user_metadata != user_data.get("user_metadata", {}):
                    await self.update_user(
                        user_data["id"],
                        user_metadata=user_metadata
                    )
                
                return {
                    "user": user_data,
                    "session": result.session.model_dump() if hasattr(result, 'session') else None,
                    "provider": provider,
                }
            
            # Otherwise, return the OAuth URL
            result = self.supabase.auth.sign_in_with_oauth({
                "provider": provider,
                "options": {
                    "redirect_to": redirect_uri or f"{settings.SUPABASE_URL}/auth/v1/callback",
                    "query_params": {
                        "access_type": "offline",
                        "prompt": "consent",
                    },
                },
            })
            
            if not result or not hasattr(result, 'url'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to initiate {provider} OAuth flow",
                )
                
            return {"url": result.url}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error with {provider} OAuth: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to authenticate with {provider}: {str(e)}",
            )
    
    async def sign_out(self, access_token: str) -> bool:
        """Sign out the current user."""
        try:
            self.supabase.auth.sign_out(access_token)
            return True
        except Exception as e:
            logger.error(f"Error signing out: {str(e)}")
            return False
    
    async def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh the user's session."""
        try:
            result = self.supabase.auth.refresh_session(refresh_token)
            return result.dict()
        except Exception as e:
            logger.error(f"Error refreshing session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not refresh session"
            )
    
    async def get_current_user_info(self, request: Request) -> Dict[str, Any]:
        """Get current user information."""
        try:
            # Get the JWT token from the request
            credentials = await HTTPBearer(auto_error=False)(request)
            if not credentials:
                # Try to get from cookies if not in Authorization header
                access_token = request.cookies.get("sb-access-token")
                if not access_token:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Could not validate credentials",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                
                # Set the credentials for the rest of the function
                credentials = HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials=access_token
                )
                
            # Verify the token and get the user info
            user = await get_current_user(request)
            
            # Get additional user info from Supabase
            user_id = user.get("sub")
            if user_id:
                supabase_user = await self.get_user_by_id(user_id)
                if supabase_user:
                    # Merge the user data
                    user.update({
                        "email": supabase_user.get("email"),
                        "email_verified": supabase_user.get("email_confirmed_at") is not None,
                        "user_metadata": supabase_user.get("user_metadata", {}),
                        "app_metadata": supabase_user.get("app_metadata", {})
                    })
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_current_user_info: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not get user information"
            )
            
            return user_info
            
        except Exception as e:
            logger.error(f"Error getting current user info: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not get user information"
            )

# Create a singleton instance of the service
supabase_auth_service = SupabaseAuthService()

# Dependency to get the current user from the request
async def get_current_active_user(
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Dependency to get the current active user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Check if email is verified if required
    if not current_user.get('email_verified'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    
    # Store user in request state for use in other dependencies
    if request:
        request.state.user = current_user
    
    return current_user
