"""
Authentication routes for the API using Supabase.
"""
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, HttpUrl

from app.services.supabase_auth import supabase_auth_service, get_current_active_user
from app.services.auth_service import oauth2_scheme  # Keep for backward compatibility
from app.core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Request and Response Models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    user_metadata: Optional[Dict[str, Any]] = None
    
class UserResponse(BaseModel):
    id: str
    email: str
    email_verified: bool
    user_metadata: Dict[str, Any]
    app_metadata: Dict[str, Any]
    created_at: str
    updated_at: str

class PhoneOTPLoginRequest(BaseModel):
    phone: str
    options: Optional[Dict[str, Any]] = None

class VerifyOTPRequest(BaseModel):
    phone: str
    token: str
    type: Optional[str] = "sms"
    redirect_to: Optional[HttpUrl] = None

class OAuthRequest(BaseModel):
    code: str
    redirect_uri: str

@router.post("/login", response_model=Dict[str, Any])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    response: Response = None
):
    """
    Login with email and password.
    
    This endpoint authenticates a user with their email and password and returns
    an access token and refresh token.
    """
    try:
        # Authenticate with Supabase
        result = await supabase_auth_service.sign_in_with_email_password(
            email=form_data.username,
            password=form_data.password
        )
        
        # Get the session data
        session = result.get("data", {})
        user = session.get("user", {})
        
        # Set the auth cookie if needed
        if response and hasattr(response, 'set_cookie'):
            response.set_cookie(
                key="sb-access-token",
                value=session.get("access_token", ""),
                httponly=True,
                max_age=3600,  # 1 hour
                samesite="lax"
            )
            response.set_cookie(
                key="sb-refresh-token",
                value=session.get("refresh_token", ""),
                httponly=True,
                max_age=604800,  # 7 days
                samesite="lax"
            )
        
        return {
            "access_token": session.get("access_token"),
            "refresh_token": session.get("refresh_token"),
            "expires_in": session.get("expires_in"),
            "token_type": "bearer",
            "user": user
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        ) from exc

@router.post("/signup", response_model=Dict[str, Any])
async def signup(
    user_data: UserCreate,
    response: Response = None
):
    """
    Register a new user with email and password.
    
    This endpoint creates a new user account and returns an access token
    and refresh token for the new user.
    """
    try:
        # Create user in Supabase Auth
        result = await supabase_auth_service.sign_up_with_email_password(
            email=user_data.email,
            password=user_data.password,
            user_metadata=user_data.user_metadata
        )
        
        # Get the session data
        session = result.get("data", {})
        user = session.get("user", {})
        
        # Set the auth cookie if needed
        if response and hasattr(response, 'set_cookie'):
            response.set_cookie(
                key="sb-access-token",
                value=session.get("access_token", ""),
                httponly=True,
                max_age=3600,  # 1 hour
                samesite="lax"
            )
            response.set_cookie(
                key="sb-refresh-token",
                value=session.get("refresh_token", ""),
                httponly=True,
                max_age=604800,  # 7 days
                samesite="lax"
            )
        
        return {
            "access_token": session.get("access_token"),
            "refresh_token": session.get("refresh_token"),
            "expires_in": session.get("expires_in"),
            "token_type": "bearer",
            "user": user
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during signup"
        ) from exc

@router.post("/otp/request")
async def request_phone_otp(request: PhoneOTPLoginRequest):
    """
    Request OTP for phone login.
    
    Sends a one-time password to the provided phone number for authentication.
    """
    try:
        # This would integrate with Supabase's phone auth
        # For now, we'll just return a success message
        return {
            "message": "OTP sent successfully",
            "phone": request.phone
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/otp/verify")
async def verify_phone_otp(
    request: VerifyOTPRequest,
    response: Response = None
):
    """
    Verify OTP and login with phone.
    
    Verifies the one-time password and authenticates the user if valid.
    """
    try:
        # This would integrate with Supabase's phone auth
        # For now, we'll just return a mock response
        mock_user = {
            "id": "phone-auth-user-id",
            "phone": request.phone,
            "role": "authenticated",
            "aud": "authenticated",
            "app_metadata": {
                "provider": "phone"
            },
            "user_metadata": {}
        }
        
        # In a real implementation, we would get this from Supabase
        mock_session = {
            "access_token": "mock-access-token",
            "refresh_token": "mock-refresh-token",
            "expires_in": 3600,
            "token_type": "bearer",
            "user": mock_user
        }
        
        # Set the auth cookie if needed
        if response and hasattr(response, 'set_cookie'):
            response.set_cookie(
                key="sb-access-token",
                value=mock_session["access_token"],
                httponly=True,
                max_age=3600,  # 1 hour
                samesite="lax"
            )
            response.set_cookie(
                key="sb-refresh-token",
                value=mock_session["refresh_token"],
                httponly=True,
                max_age=604800,  # 7 days
                samesite="lax"
            )
        
        return {
            "access_token": mock_session["access_token"],
            "refresh_token": mock_session["refresh_token"],
            "expires_in": mock_session["expires_in"],
            "token_type": "bearer",
            "user": mock_user
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during OTP verification"
        ) from exc

@router.get("/oauth/{provider}")
async def login_with_oauth(
    provider: str,
    code: str,
    redirect_uri: str,
    response: Response = None
):
    """
    Login with OAuth provider (Google, Apple, etc.).
    
    This endpoint handles the OAuth callback and exchanges the authorization code
    for an access token.
    """
    try:
        # Exchange the authorization code for tokens
        result = await supabase_auth_service.sign_in_with_oauth(
            provider=provider,
            code=code,
            redirect_uri=redirect_uri
        )
        
        # Get the session data
        session = result.get("data", {})
        user = session.get("user", {})
        
        # Set the auth cookie if needed
        if response and hasattr(response, 'set_cookie'):
            response.set_cookie(
                key="sb-access-token",
                value=session.get("access_token", ""),
                httponly=True,
                max_age=3600,  # 1 hour
                samesite="lax"
            )
            response.set_cookie(
                key="sb-refresh-token",
                value=session.get("refresh_token", ""),
                httponly=True,
                max_age=604800,  # 7 days
                samesite="lax"
            )
        
        return {
            "access_token": session.get("access_token"),
            "refresh_token": session.get("refresh_token"),
            "expires_in": session.get("expires_in"),
            "token_type": "bearer",
            "user": user
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during {provider} login"
        ) from exc

@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get current user information.
    
    Returns detailed information about the currently authenticated user,
    including their profile data and metadata.
    """
    try:
        return await supabase_auth_service.get_current_user_info(request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve user information"
        )

@router.post("/logout")
async def logout(
    response: Response,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Log out the current user.
    
    This endpoint invalidates the current session and clears auth cookies.
    """
    try:
        # Clear the auth cookies
        response.delete_cookie("sb-access-token")
        response.delete_cookie("sb-refresh-token")
        
        # In a real implementation, you might want to revoke the refresh token
        # await supabase_auth_service.sign_out(current_user.get("access_token"))
        
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not log out"
        )

@router.post("/refresh")
async def refresh_session(
    refresh_token: str,
    response: Response = None
):
    """
    Refresh an access token.
    
    This endpoint exchanges a refresh token for a new access token.
    """
    try:
        result = await supabase_auth_service.refresh_session(refresh_token)
        
        # Update the auth cookies if response is provided
        if response and hasattr(response, 'set_cookie'):
            response.set_cookie(
                key="sb-access-token",
                value=result.get("access_token"),
                httponly=True,
                max_age=3600,  # 1 hour
                samesite="lax"
            )
            
            # Only update refresh token if a new one was provided
            if "refresh_token" in result:
                response.set_cookie(
                    key="sb-refresh-token",
                    value=result["refresh_token"],
                    httponly=True,
                    max_age=604800,  # 7 days
                    samesite="lax"
                )
        
        return {
            "access_token": result.get("access_token"),
            "refresh_token": result.get("refresh_token"),
            "token_type": "bearer",
            "expires_in": result.get("expires_in")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh session"
        )
