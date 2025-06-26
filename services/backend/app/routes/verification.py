"""Verification routes for user email and phone verification."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.endpoints.verification import (
    check_verification_status,
    resend_verification,
    verify_phone_with_code,
)
from app.schemas.verification import (
    VerificationResendRequest,
    PhoneVerificationRequest,
)

# Create router
router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Include verification endpoints
router.add_api_route(
    "/status/{verification_type}",
    check_verification_status,
    methods=["GET"],
    tags=["verification"],
    summary="Check verification status",
    description="Check the verification status of a user's email or phone number.",
)

router.add_api_route(
    "/resend",
    resend_verification,
    methods=["POST"],
    tags=["verification"],
    summary="Resend verification",
    description="Resend a verification email or SMS to the user.",
)

router.add_api_route(
    "/verify-phone",
    verify_phone_with_code,
    methods=["POST"],
    tags=["verification"],
    summary="Verify phone with OTP",
    description="Verify a phone number with the provided OTP code.",
)

# For backward compatibility with the endpoints module
check_verification_status_endpoint = check_verification_status
resend_verification_endpoint = resend_verification
verify_phone_with_code_endpoint = verify_phone_with_code
