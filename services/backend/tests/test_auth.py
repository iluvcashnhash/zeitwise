"""Tests for authentication endpoints."""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app
from app.core.config import settings

# Test client
client = TestClient(app)

# Test data
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"
TEST_PHONE = "+1234567890"
TEST_OTP = "123456"
TEST_OAUTH_CODE = "test_oauth_code"
TEST_REDIRECT_URI = "http://localhost:3000/auth/callback"

# Mock responses
MOCK_USER = {
    "id": "test-user-id",
    "email": TEST_EMAIL,
    "user_metadata": {},
    "app_metadata": {}
}

MOCK_SESSION = {
    "access_token": "test-access-token",
    "refresh_token": "test-refresh-token",
    "user": MOCK_USER
}

# Test cases

def test_login_success():
    """Test successful login with email and password."""
    with patch("app.services.auth_service.AuthService.sign_in_with_email_password") as mock_login:
        mock_login.return_value = {
            "access_token": MOCK_SESSION["access_token"],
            "refresh_token": MOCK_SESSION["refresh_token"],
            "user": MOCK_USER
        }
        
        response = client.post(
            "/api/auth/login",
            data={"username": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["access_token"] == MOCK_SESSION["access_token"]
        assert data["refresh_token"] == MOCK_SESSION["refresh_token"]
        assert data["user"]["email"] == TEST_EMAIL

def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    with patch("app.services.auth_service.AuthService.sign_in_with_email_password") as mock_login:
        mock_login.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
        
        response = client.post(
            "/api/auth/login",
            data={"username": TEST_EMAIL, "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Incorrect email or password"

def test_signup_success():
    """Test successful user registration."""
    with patch("app.services.auth_service.AuthService.sign_up_with_email_password") as mock_signup:
        mock_signup.return_value = {
            "id": "test-user-id",
            "email": TEST_EMAIL,
            "email_confirmed": False,
            "user_metadata": {}
        }
        
        response = client.post(
            "/api/auth/signup",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "user_metadata": {"name": "Test User"}
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == TEST_EMAIL
        assert data["id"] == "test-user-id"

def test_request_phone_otp_success():
    """Test successful OTP request for phone login."""
    with patch("app.services.auth_service.AuthService.sign_in_with_phone_otp") as mock_otp:
        mock_otp.return_value = {"message": "OTP sent successfully"}
        
        response = client.post(
            "/api/auth/login/phone/request",
            json={"phone": TEST_PHONE}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "OTP sent successfully"

def test_verify_phone_otp_success():
    """Test successful OTP verification."""
    with patch("app.services.auth_service.AuthService.verify_phone_otp") as mock_verify:
        mock_verify.return_value = {
            "access_token": MOCK_SESSION["access_token"],
            "refresh_token": MOCK_SESSION["refresh_token"],
            "user": MOCK_USER
        }
        
        response = client.post(
            "/api/auth/login/phone/verify",
            json={
                "phone": TEST_PHONE,
                "token": TEST_OTP
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["access_token"] == MOCK_SESSION["access_token"]
        assert data["refresh_token"] == MOCK_SESSION["refresh_token"]
        assert data["user"]["email"] == TEST_EMAIL

def test_oauth_login():
    """Test OAuth login flow."""
    with patch("app.services.auth_service.AuthService.sign_in_with_oauth") as mock_oauth:
        mock_oauth.return_value = {
            "message": "OAuth flow initiated",
            "url": f"{settings.SUPABASE_URL}/auth/v1/authorize?provider=google"
        }
        
        response = client.post(
            "/api/auth/login/google",
            json={
                "code": TEST_OAUTH_CODE,
                "redirect_uri": TEST_REDIRECT_URI
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "url" in data
        assert "google" in data["url"]

@pytest.mark.asyncio
async def test_get_current_user_success():
    """Test getting current user with valid token."""
    with patch("app.services.auth_service.AuthService.get_current_user") as mock_user:
        mock_user.return_value = MOCK_USER
        
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {MOCK_SESSION['access_token']}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == TEST_EMAIL
        assert data["id"] == "test-user-id"

@pytest.mark.asyncio
async def test_get_current_user_unauthorized():
    """Test getting current user with invalid token."""
    with patch("app.services.auth_service.AuthService.get_current_user") as mock_user:
        mock_user.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
        
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
