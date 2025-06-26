import pytest
from unittest.mock import AsyncMock, patch, MagicMock, call, ANY
import json
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import time
import asyncio

from fastapi import HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.core import security
from app.core.config import settings

# Mock request object for testing
class MockRequest:
    def __init__(self, headers=None, state=None):
        self.headers = headers or {}
        self.state = state or type('State', (), {})()
        self.app = MagicMock()
        self.app.logger = MagicMock()

# Helper function to run async tests
def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper

# Test data
MOCK_JWKS = {
    "keys": [
        {
            "kty": "RSA",
            "n": "test_n_value",
            "e": "AQAB",
            "kid": "test_kid",
            "alg": "RS256",
            "use": "sig"
        }
    ]
}

MOCK_PAYLOAD = {
    "sub": "auth0|1234567890",
    "email": "test@example.com",
    "email_verified": True,
    "phone_verified": False,
    "role": "user",
    "app_metadata": {"roles": ["user"]},
    "user_metadata": {"name": "Test User"},
    "aud": "authenticated",
    "iss": f"{settings.SUPABASE_URL}/auth/v1" if settings.SUPABASE_URL else "https://example.com/auth/v1",
    "exp": int(time.time()) + 3600,
    "iat": int(time.time()),
    "nbf": int(time.time())
}

@pytest.fixture
def mock_http_client():
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_JWKS
        mock_response.raise_for_status.return_value = None
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        yield mock_client
        mock_client.return_value.__aenter__.return_value.raise_for_status.return_value = None
        yield mock_client

@pytest.fixture
def mock_jwt_decode():
    with patch('jwt.decode') as mock_decode:
        mock_decode.return_value = MOCK_PAYLOAD
        yield mock_decode

@pytest.fixture
def mock_get_unverified_header():
    with patch('jwt.get_unverified_header') as mock_header:
        mock_header.return_value = {"kid": "test_kid", "alg": "RS256"}
        yield mock_header

@pytest.fixture
def mock_async_client():
    """Fixture to mock httpx.AsyncClient."""
    with patch('httpx.AsyncClient') as mock_client:
        # Create a mock response
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = AsyncMock(return_value=MOCK_JWKS)
        
        # Configure the client to return the mock response
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        yield mock_client, mock_response

@pytest.mark.asyncio
async def test_get_jwks_success(mock_async_client):
    """Test successful retrieval of JWKS."""
    mock_client, mock_response = mock_async_client
    
    # Call the function
    jwks = await security.get_jwks()
    
    # Verify the results
    assert jwks == MOCK_JWKS
    
    # Verify the client was used correctly
    mock_client.return_value.__aenter__.assert_awaited_once()
    mock_client.return_value.__aexit__.assert_awaited_once()
    
    # Verify the request was made correctly
    mock_client.return_value.__aenter__.return_value.get.assert_awaited_once_with(
        f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    )
    
    # Verify the response was handled correctly
    mock_response.raise_for_status.assert_awaited_once()
    mock_response.json.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_jwks_failure():
    """Test failure when retrieving JWKS."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Network error")
        with pytest.raises(HTTPException) as exc_info:
            await security.get_jwks()
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

@pytest.mark.asyncio
async def test_get_public_key_success():
    """Test getting public key with valid key ID."""
    with patch('app.core.security.get_jwks', return_value=MOCK_JWKS) as mock_get_jwks:
        # First call - should call get_jwks
        key = await security.get_public_key("test_kid")
        assert key == MOCK_JWKS["keys"][0]
        
        # Clear the cache to simulate a fresh call
        security.jwks_cache.clear()
        
        # Second call - should call get_jwks again
        key = await security.get_public_key("test_kid")
        assert key == MOCK_JWKS["keys"][0]
        
        # Should have been called twice (no caching in this test)
        assert mock_get_jwks.call_count == 2

@pytest.mark.asyncio
async def test_get_public_key_not_found():
    """Test getting public key with invalid key ID."""
    with patch('app.core.security.get_jwks') as mock_get_jwks:
        mock_get_jwks.return_value = MOCK_JWKS
        with pytest.raises(HTTPException) as exc_info:
            await security.get_public_key("invalid_kid")
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_decode_jwt_success():
    """Test successful JWT decoding."""
    with patch('app.core.security.get_public_key') as mock_get_pub_key, \
         patch('jose.jwt.get_unverified_header') as mock_header, \
         patch('jose.jwt.decode') as mock_decode:
        # Setup mocks
        mock_header.return_value = {"kid": "test_kid", "alg": "RS256"}
        mock_get_pub_key.return_value = {"kty": "RSA", "n": "test_n_value", "e": "AQAB", "alg": "RS256"}
        mock_decode.return_value = MOCK_PAYLOAD
        
        # Call the function
        payload = await security.decode_jwt("test_token")
        
        # Verify the results
        assert payload == MOCK_PAYLOAD
        mock_header.assert_called_once_with("test_token")
        mock_decode.assert_called_once()

@pytest.mark.asyncio
async def test_decode_jwt_missing_kid():
    """Test JWT decoding with missing key ID."""
    with patch('jose.jwt.get_unverified_header') as mock_header:
        mock_header.return_value = {}
        with pytest.raises(HTTPException) as exc_info:
            await security.decode_jwt("test_token")
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "missing key ID" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_get_current_user_success():
    """Test getting current user with valid token."""
    mock_request = MockRequest()
    mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test_token")
    mock_payload = MOCK_PAYLOAD.copy()
    
    with patch('app.core.security.decode_jwt', return_value=mock_payload) as mock_decode:
        user = await security.get_current_user(mock_request, mock_credentials)
        
        # Verify user data
        assert user["sub"] == mock_payload["sub"]
        assert user["email"] == mock_payload["email"]
        assert user["email_verified"] is True
        assert user["phone_verified"] is False
        assert user["role"] == "user"
        assert "app_metadata" in user
        assert "user_metadata" in user
        
        # Verify request state was updated
        assert hasattr(mock_request.state, 'user')
        assert mock_request.state.user == user
        
        # Verify decode was called with correct args
        mock_decode.assert_called_once_with("test_token")

@pytest.mark.asyncio
async def test_get_current_user_missing_credentials():
    """Test getting current user with missing credentials."""
    mock_request = MockRequest()
    with pytest.raises(HTTPException) as exc_info:
        await security.get_current_user(mock_request, None)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """Test getting current user with invalid token."""
    mock_request = MockRequest()
    mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")
    
    with patch('app.core.security.decode_jwt', side_effect=JWTError("Invalid token")) as mock_decode:
        with pytest.raises(HTTPException) as exc_info:
            await security.get_current_user(mock_request, mock_credentials)
            
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid authentication credentials" in str(exc_info.value.detail)
        assert "WWW-Authenticate" in exc_info.value.headers
        mock_decode.assert_called_once_with("invalid_token")

@pytest.mark.asyncio
async def test_get_required_roles():
    """Test role-based access control"""
    mock_request = MockRequest()
    mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
    
    # Setup mock payload with admin role
    admin_payload = MOCK_PAYLOAD.copy()
    admin_payload["app_metadata"]["roles"] = ["admin"]
    
    # Setup mock payload with user role
    user_payload = MOCK_PAYLOAD.copy()
    user_payload["app_metadata"]["roles"] = ["user"]
    
    # Test admin access with admin role
    with patch('app.core.security.decode_jwt', return_value=admin_payload):
        admin_checker = security.get_required_roles("admin")
        user = await admin_checker(await security.get_current_user(mock_request, mock_credentials))
        assert user["sub"] == admin_payload["sub"]
    
    # Test user access with user role
    with patch('app.core.security.decode_jwt', return_value=user_payload):
        user_checker = security.get_required_roles("user")
        user = await user_checker(await security.get_current_user(mock_request, mock_credentials))
        assert user["sub"] == user_payload["sub"]
    
    # Test admin access with user role (should fail)
    with patch('app.core.security.decode_jwt', return_value=user_payload):
        admin_checker = security.get_required_roles("admin")
        with pytest.raises(HTTPException) as exc_info:
            await admin_checker(await security.get_current_user(mock_request, mock_credentials))
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Insufficient permissions" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_verify_token_claims():
    """Test token claims verification"""
    now = int(time.time())
    
    # Test valid token
    valid_payload = {
        "sub": "user123",
        "aud": "authenticated",
        "iss": f"{settings.SUPABASE_URL}/auth/v1" if settings.SUPABASE_URL else "https://example.com/auth/v1",
        "exp": now + 3600,
        "nbf": now - 10,
        "iat": now - 5
    }
    
    # Should not raise
    security.verify_token_claims(valid_payload)
    
    # Test expired token
    expired_payload = valid_payload.copy()
    expired_payload["exp"] = now - 10
    with pytest.raises(JWTError, match="Token has expired"):
        security.verify_token_claims(expired_payload)
    
    # Test not yet valid token
    future_payload = valid_payload.copy()
    future_payload["nbf"] = now + 10
    with pytest.raises(JWTError, match="Token not yet valid"):
        security.verify_token_claims(future_payload)
    
    # Test invalid audience
    invalid_aud_payload = valid_payload.copy()
    invalid_aud_payload["aud"] = "invalid_audience"
    with pytest.raises(JWTError, match="Invalid audience"):
        security.verify_token_claims(invalid_aud_payload)
    
    # Test invalid issuer
    if settings.SUPABASE_URL:  # Only test if SUPABASE_URL is set
        invalid_iss_payload = valid_payload.copy()
        invalid_iss_payload["iss"] = "https://invalid-issuer.com/auth/v1"
        with pytest.raises(JWTError, match="Invalid issuer"):
            security.verify_token_claims(invalid_iss_payload)

@pytest.mark.asyncio
async def test_decode_jwt_expired():
    """Test JWT decoding with expired token."""
    with patch('jose.jwt.decode') as mock_decode:
        mock_decode.side_effect = jwt.JWTError("Invalid signature")
        with pytest.raises(HTTPException) as exc_info:
            await security.decode_jwt("expired.token.here")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token: Error decoding token headers" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_get_public_key_error_handling():
    """Test error handling when getting public key fails."""
    # First call to populate cache with empty keys
    with patch('app.core.security.jwks_cache', {}):
        with patch('app.core.security.get_jwks') as mock_get_jwks:
            mock_get_jwks.return_value = {"keys": []}  # No keys in JWKS
            with pytest.raises(HTTPException) as exc_info:
                await security.get_public_key("nonexistent_kid")
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid token: unknown key ID" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_get_current_user_malformed_token():
    """Test getting current user with malformed token."""
    with patch('app.core.security.decode_jwt') as mock_decode:
        mock_decode.side_effect = Exception("Malformed token")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="malformed.token.here")
        
        with pytest.raises(HTTPException) as exc_info:
            await security.get_current_user(credentials)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in str(exc_info.value.detail)
