"""
Authentication routes for the API.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from app.services.auth_service import auth_service, oauth2_scheme

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
    user_metadata: Optional[dict] = None

class PhoneOTPRequest(BaseModel):
    phone: str

class VerifyOTPRequest(BaseModel):
    phone: str
    token: str

class OAuthRequest(BaseModel):
    code: str
    redirect_uri: str

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """Login with email and password."""
    try:
        result = await auth_service.sign_in_with_email_password(
            email=form_data.username,
            password=form_data.password
        )
        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": "bearer",
            "user": result["user"]
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        ) from exc

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    """Register a new user with email and password."""
    try:
        result = await auth_service.sign_up_with_email_password(
            email=user_data.email,
            password=user_data.password,
            user_metadata=user_data.user_metadata
        )
        return result
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during signup"
        ) from exc

@router.post("/login/phone/request")
async def request_phone_otp(request: PhoneOTPRequest):
    """Request OTP for phone login."""
    try:
        return await auth_service.sign_in_with_phone_otp(phone=request.phone)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while requesting OTP"
        ) from exc

@router.post("/login/phone/verify", response_model=Token)
async def verify_phone_otp(request: VerifyOTPRequest):
    """Verify OTP and login with phone."""
    try:
        result = await auth_service.verify_phone_otp(
            phone=request.phone,
            token=request.token
        )
        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": "bearer",
            "user": result["user"]
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during OTP verification"
        ) from exc

@router.post("/login/{provider}")
async def login_with_oauth(provider: str, request: OAuthRequest):
    """Login with OAuth provider (Google, Apple, etc.)."""
    try:
        return await auth_service.sign_in_with_oauth(
            provider=provider,
            code=request.code,
            redirect_uri=request.redirect_uri
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during {provider} login"
        ) from exc

@router.get("/me")
async def get_current_user_info(
    token: str = Depends(oauth2_scheme)
):
    """Get current user information."""
    try:
        return await auth_service.get_current_user(token)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching user information"
        ) from exc
