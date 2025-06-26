"""API endpoints for user verification (email/phone)."""
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user_model import User
from app.schemas.verification import (
    VerificationStatusResponse,
    VerificationResendRequest,
    VerificationResendResponse,
    PhoneVerificationRequest,
    PhoneVerificationResponse,
)
from app.services.verification_service import get_verification_service, VerificationService

router = APIRouter()
security = HTTPBearer()

@router.get(
    "/status/{verification_type}",
    response_model=VerificationStatusResponse,
    summary="Check verification status",
    description="Check the verification status of a user's email or phone number.",
    responses={
        200: {"description": "Verification status retrieved successfully"},
        400: {"description": "Invalid verification type"},
        401: {"description": "Unauthorized"},
        404: {"description": "User not found"},
    },
)
async def check_verification_status(
    verification_type: str,
    current_user: User = Depends(get_current_user),
    verification_service: VerificationService = Depends(get_verification_service),
) -> Dict[str, Any]:
    """
    Check the verification status of the current user's email or phone number.
    
    Args:
        verification_type: Type of verification to check ('email' or 'phone')
        current_user: The currently authenticated user
        verification_service: The verification service
        
    Returns:
        Verification status and related information
    """
    result = await verification_service.check_verification_status(
        str(current_user.id), 
        verification_type
    )
    return {"success": True, "data": result}

@router.post(
    "/resend",
    response_model=VerificationResendResponse,
    summary="Resend verification",
    description="Resend a verification email or SMS to the user.",
    responses={
        200: {"description": "Verification email/SMS sent successfully"},
        400: {"description": "Invalid verification type or missing contact info"},
        401: {"description": "Unauthorized"},
        404: {"description": "User not found"},
    },
)
async def resend_verification(
    request: VerificationResendRequest,
    current_user: User = Depends(get_current_user),
    verification_service: VerificationService = Depends(get_verification_service),
) -> Dict[str, Any]:
    """
    Resend a verification email or SMS to the current user.
    
    Args:
        request: The verification request data
        current_user: The currently authenticated user
        verification_service: The verification service
        
    Returns:
        Confirmation that the verification was sent
    """
    result = await verification_service.resend_verification(
        str(current_user.id),
        request.verification_type,
        request.redirect_url
    )
    return {"success": True, "data": result}

@router.post(
    "/verify-phone",
    response_model=PhoneVerificationResponse,
    summary="Verify phone with OTP",
    description="Verify a phone number with the provided OTP code.",
    responses={
        200: {"description": "Phone number verified successfully"},
        400: {"description": "Invalid or expired verification code"},
        401: {"description": "Unauthorized"},
        404: {"description": "User not found"},
    },
)
async def verify_phone_with_code(
    request: PhoneVerificationRequest,
    verification_service: VerificationService = Depends(get_verification_service),
) -> Dict[str, Any]:
    """
    Verify a phone number with the provided OTP code.
    
    Args:
        request: The phone verification request data
        verification_service: The verification service
        
    Returns:
        Verification result with user information
    """
    result = await verification_service.verify_phone_with_code(
        request.phone,
        request.token
    )
    return {"success": True, "data": result}
