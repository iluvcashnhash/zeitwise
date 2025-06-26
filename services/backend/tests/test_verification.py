"""Tests for verification endpoints and services."""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.user_model import User
from app.schemas.verification import VerificationStatus, VerificationResendRequest, PhoneVerificationRequest
from app.core.config import settings

client = TestClient(app)

# Test data
TEST_USER_ID = "123e4567-e89b-12d3-a456-426614174000"
TEST_EMAIL = "test@example.com"
TEST_PHONE = "+1234567890"
TEST_OTP = "123456"

# Fixtures
@pytest.fixture
def mock_current_user():
    """Mock the current user for authentication."""
    return User(
        id=TEST_USER_ID,
        email=TEST_EMAIL,
        is_verified=False,
        metadata_={"providers": ["email"], "provider": "email"}
    )

@pytest.fixture
def mock_verification_status():
    """Mock verification status response."""
    return {
        "user_id": TEST_USER_ID,
        "type": "email",
        "is_verified": False,
        "verified_at": None,
        "contact": TEST_EMAIL,
        "provider": "email"
    }

# Test cases
class TestVerificationEndpoints:
    """Test verification endpoints."""
    
    @patch("app.api.deps.get_current_user")
    def test_check_verification_status(self, mock_get_user, mock_current_user):
        """Test checking verification status."""
        # Setup
        mock_get_user.return_value = mock_current_user
        
        # Test with email verification
        with patch("app.services.verification_service.VerificationService.check_verification_status") as mock_check:
            mock_check.return_value = VerificationStatus(**{
                "user_id": TEST_USER_ID,
                "type": "email",
                "is_verified": False,
                "verified_at": None,
                "contact": TEST_EMAIL,
                "provider": "email"
            })
            
            response = client.get(
                f"/api/verification/status/email",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["user_id"] == TEST_USER_ID
            assert data["data"]["type"] == "email"
    
    @patch("app.api.deps.get_current_user")
    def test_resend_verification(self, mock_get_user, mock_current_user):
        """Test resending verification email."""
        # Setup
        mock_get_user.return_value = mock_current_user
        request_data = {"verification_type": "email"}
        
        with patch("app.services.verification_service.VerificationService.resend_verification") as mock_resend:
            mock_resend.return_value = {
                "message": "Verification email sent",
                "contact": TEST_EMAIL,
                "type": "email"
            }
            
            response = client.post(
                "/api/verification/resend",
                json=request_data,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["message"] == "Verification email sent"
    
    def test_verify_phone_with_code(self):
        """Test verifying phone with OTP code."""
        request_data = {
            "phone": TEST_PHONE,
            "token": TEST_OTP
        }
        
        with patch("app.services.verification_service.VerificationService.verify_phone_with_code") as mock_verify:
            mock_verify.return_value = {
                "success": True,
                "message": "Phone number verified successfully",
                "user_id": TEST_USER_ID,
                "phone": TEST_PHONE,
                "is_verified": True
            }
            
            response = client.post(
                "/api/verification/verify-phone",
                json=request_data
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["is_verified"] is True

# Test error cases
class TestVerificationErrors:
    """Test verification error cases."""
    
    def test_invalid_verification_type(self):
        """Test with invalid verification type."""
        response = client.get(
            "/api/verification/status/invalid",
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_unauthorized_access(self):
        """Test accessing protected endpoint without auth."""
        response = client.get("/api/verification/status/email")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

# Test service layer
class TestVerificationService:
    """Test verification service methods."""
    
    @pytest.mark.asyncio
    async def test_check_verification_status(self, db: AsyncSession, mock_verification_status):
        """Test checking verification status in service layer."""
        from app.services.verification_service import VerificationService
        from app.services.supabase_auth import supabase_auth_service
        
        # Mock the supabase auth service
        with patch.object(supabase_auth_service, 'check_email_verification') as mock_check:
            mock_check.return_value = {
                'user_id': TEST_USER_ID,
                'email': TEST_EMAIL,
                'is_verified': True,
                'verified_at': '2023-01-01T00:00:00Z',
                'provider': 'email'
            }
            
            service = VerificationService(db)
            result = await service.check_verification_status(TEST_USER_ID, "email")
            
            assert result["user_id"] == TEST_USER_ID
            assert result["is_verified"] is True
            assert result["type"] == "email"
    
    @pytest.mark.asyncio
    async def test_resend_verification(self, db: AsyncSession):
        """Test resending verification in service layer."""
        from app.services.verification_service import VerificationService
        from app.services.supabase_auth import supabase_auth_service
        
        # Mock the supabase auth service
        with patch.object(supabase_auth_service, 'send_email_verification') as mock_send:
            mock_send.return_value = {
                'success': True,
                'message': 'Verification email sent',
                'email': TEST_EMAIL
            }
            
            service = VerificationService(db)
            result = await service.resend_verification(
                TEST_USER_ID,
                "email",
                "https://example.com/verify"
            )
            
            assert result["success"] is True
            assert result["message"] == "Verification email sent"
            assert result["contact"] == TEST_EMAIL
