"""Pydantic models for verification endpoints."""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, validator, EmailStr


class VerificationType(str, Enum):
    """Types of verification methods."""
    EMAIL = "email"
    PHONE = "phone"


class VerificationStatus(BaseModel):
    """Verification status response model."""
    user_id: str = Field(..., description="The user's ID")
    type: VerificationType = Field(..., description="Type of verification (email/phone)")
    is_verified: bool = Field(..., description="Whether the contact method is verified")
    verified_at: Optional[datetime] = Field(None, description="When the verification was completed")
    contact: Optional[str] = Field(None, description="The email or phone number being verified")
    provider: Optional[str] = Field(None, description="The authentication provider")


class VerificationStatusResponse(BaseModel):
    """Response model for verification status check."""
    success: bool = Field(True, description="Whether the request was successful")
    data: VerificationStatus = Field(..., description="Verification status details")


class VerificationResendRequest(BaseModel):
    """Request model for resending verification."""
    verification_type: VerificationType = Field(
        ..., 
        description="Type of verification to resend (email/phone)"
    )
    redirect_url: Optional[HttpUrl] = Field(
        None, 
        description="URL to redirect to after verification (for email)"
    )


class VerificationResendResponse(BaseModel):
    """Response model for resend verification request."""
    success: bool = Field(True, description="Whether the request was successful")
    data: Dict[str, Any] = Field(..., description="Details about the sent verification")


class PhoneVerificationRequest(BaseModel):
    """Request model for phone verification with OTP."""
    phone: str = Field(..., description="Phone number with country code (e.g., +1234567890)")
    token: str = Field(..., description="OTP token received via SMS")


class PhoneVerificationResponse(BaseModel):
    """Response model for phone verification."""
    success: bool = Field(True, description="Whether the verification was successful")
    data: Dict[str, Any] = Field(..., description="Verification result details")


class VerificationEventType(str, Enum):
    """Types of verification events."""
    EMAIL_VERIFICATION_SENT = "email_verification_sent"
    PHONE_VERIFICATION_SENT = "phone_verification_sent"
    EMAIL_VERIFIED = "email_verified"
    PHONE_VERIFIED = "phone_verified"


class VerificationWebhookData(BaseModel):
    """Data model for verification webhook events."""
    user_id: str = Field(..., description="The user's ID")
    event_type: VerificationEventType = Field(..., description="Type of verification event")
    timestamp: datetime = Field(..., description="When the event occurred")
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata about the event"
    )


class VerificationWebhookRequest(BaseModel):
    """Request model for verification webhook events."""
    type: str = Field(..., description="Type of webhook event")
    event: VerificationWebhookData = Field(..., description="Event data")
    created_at: datetime = Field(..., description="When the webhook was created")
