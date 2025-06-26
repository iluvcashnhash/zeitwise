import pytest
from unittest.mock import AsyncMock, patch, MagicMock, call
import json
from jose import jwt
from datetime import datetime, timedelta
import time
import asyncio

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.core import security
from app.core.config import settings

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
    "role": "user",
    "app_metadata": {},
    "user_metadata": {},
    "aud": "authenticated",
    "iss": f"{settings.SUPABASE_URL}/auth/v1",
    "exp": int(time.time()) + 3600
}

@pytest.fixture
def mock_http_client():
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value.json.return_value = MOCK_JWKS
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
    mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test_token")
    with patch('app.core.security.decode_jwt') as mock_decode:
        mock_decode.return_value = MOCK_PAYLOAD
        user = await security.get_current_user(mock_credentials)
        assert user["sub"] == MOCK_PAYLOAD["sub"]
        assert user["email"] == MOCK_PAYLOAD["email"]

@pytest.mark.asyncio
async def test_get_current_user_missing_credentials():
    """Test getting current user with missing credentials."""
    with pytest.raises(HTTPException) as exc_info:
        await security.get_current_user(None)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """Test getting current user with invalid token."""
    mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")
    with patch('app.core.security.decode_jwt') as mock_decode:
        mock_decode.side_effect = HTTPException(status_code=401, detail="Invalid token")
        with pytest.raises(HTTPException) as exc_info:
            await security.get_current_user(mock_credentials)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_decode_jwt_invalid_signature():
    """Test JWT decoding with invalid signature."""
    with patch('jose.jwt.decode') as mock_decode:
        mock_decode.side_effect = jwt.JWTError("Invalid signature")
        with pytest.raises(HTTPException) as exc_info:
            await security.decode_jwt("invalid.token.here")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token: Error decoding token headers" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_decode_jwt_expired():
    """Test JWT decoding with expired token."""
    with patch('jose.jwt.decode') as mock_decode:
        mock_decode.side_effect = jwt.ExpiredSignatureError("Token expired")
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
