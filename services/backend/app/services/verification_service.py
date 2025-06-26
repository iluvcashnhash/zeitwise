"""Service for handling user verification (email/phone)."""
import logging
from typing import Dict, Optional, Union

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user_model import User
from app.schemas.auth_provider import AuthProvider, is_email_provider, is_phone_provider
from app.services.supabase_auth import supabase_auth_service
from app.services.user_sync import UserSyncService

logger = logging.getLogger(__name__)

class VerificationService:
    """Service for handling user verification (email/phone)."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_sync = UserSyncService(db)
    
    async def check_verification_status(
        self, 
        user_id: str,
        verification_type: str = "email"
    ) -> Dict[str, Any]:
        """
        Check the verification status of a user's email or phone.
        
        Args:
            user_id: The user's ID
            verification_type: Type of verification to check ('email' or 'phone')
            
        Returns:
            Dict containing verification status and user data
            
        Raises:
            HTTPException: If the operation fails
        """
        verification_type = verification_type.lower()
        if verification_type not in ["email", "phone"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification type. Must be 'email' or 'phone'."
            )
        
        try:
            # First, sync the user to ensure we have the latest data
            user = await self.user_sync.sync_user_from_supabase(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check verification status from Supabase
            if verification_type == "email":
                supabase_data = await supabase_auth_service.check_email_verification(user_id)
                verification_field = "email_verified"
                contact_field = "email"
            else:
                supabase_data = await supabase_auth_service.check_phone_verification(user_id)
                verification_field = "phone_verified"
                contact_field = "phone"
            
            # Update local user metadata if needed
            metadata = user.metadata_.copy()
            needs_update = False
            
            if metadata.get(verification_field) != supabase_data["is_verified"]:
                metadata[verification_field] = supabase_data["is_verified"]
                needs_update = True
            
            if needs_update:
                user.metadata_ = metadata
                self.db.add(user)
                await self.db.commit()
                await self.db.refresh(user)
            
            return {
                "user_id": user_id,
                "type": verification_type,
                "is_verified": supabase_data["is_verified"],
                "verified_at": supabase_data.get("verified_at"),
                "contact": supabase_data.get(verification_type),
                "provider": supabase_data.get("provider"),
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking {verification_type} verification status: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to check {verification_type} verification status",
            )
    
    async def resend_verification(
        self, 
        user_id: str, 
        verification_type: str = "email",
        redirect_url: str = None
    ) -> Dict[str, Any]:
        """
        Resend a verification email or SMS to the user.
        
        Args:
            user_id: The user's ID
            verification_type: Type of verification to resend ('email' or 'phone')
            redirect_url: URL to redirect to after verification (for email)
            
        Returns:
            Dict containing the result of the operation
            
        Raises:
            HTTPException: If the operation fails
        """
        verification_type = verification_type.lower()
        if verification_type not in ["email", "phone"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification type. Must be 'email' or 'phone'."
            )
        
        try:
            # Get the user from Supabase to ensure they exist
            user_data = await supabase_auth_service.get_user_info(user_id)
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            contact = user_data.get("email" if verification_type == "email" else "phone")
            if not contact:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User does not have a {verification_type} address"
                )
            
            # Send the verification email or SMS
            if verification_type == "email":
                result = await supabase_auth_service.send_email_verification(
                    contact,
                    redirect_to=redirect_url
                )
            else:
                result = await supabase_auth_service.send_phone_verification(contact)
            
            return {
                "success": True,
                "message": f"Verification {verification_type} sent",
                "contact": contact,
                "type": verification_type,
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error sending {verification_type} verification: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to send {verification_type} verification",
            )
    
    async def verify_phone_with_code(
        self,
        phone: str,
        token: str
    ) -> Dict[str, Any]:
        """
        Verify a phone number with the provided OTP token.
        
        Args:
            phone: The phone number to verify (with country code, e.g., +1234567890)
            token: The OTP token received via SMS
            
        Returns:
            Dict containing the verification result
            
        Raises:
            HTTPException: If verification fails
        """
        try:
            # Verify the OTP with Supabase
            result = await supabase_auth_service.verify_phone_otp(phone, token)
            
            if not result.get("success"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.get("message", "Invalid or expired verification code"),
                )
            
            # Get the user ID from the result or session
            user_id = result.get("user", {}).get("id")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not identify user from verification",
                )
            
            # Sync the user to update verification status
            user = await self.user_sync.sync_user_from_supabase(user_id)
            
            return {
                "success": True,
                "message": "Phone number verified successfully",
                "user_id": user_id,
                "phone": phone,
                "is_verified": True,
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verifying phone: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to verify phone number",
            )

# Dependency for FastAPI
def get_verification_service(db: AsyncSession) -> VerificationService:
    return VerificationService(db)
