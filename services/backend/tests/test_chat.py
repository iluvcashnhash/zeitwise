"""Tests for chat endpoints."""
import pytest
from fastapi import status
from unittest.mock import patch, MagicMock, AsyncMock
from app.schemas.requests import Message, MessageRole
from app.schemas.responses import ChatMessageResponse, ChatResponse
from app.routes.chat import chat_service

# Test data
TEST_MESSAGE = Message(role=MessageRole.USER, content="Hello, world!")
TEST_CHAT_REQUEST = {
    "messages": [{"role": "user", "content": "Hello, world!"}],
    "persona_id": "socrates",
    "temperature": 0.7
}

# Mock the get_current_user dependency
def mock_get_current_user():
    return {
        "user_id": "test-user", 
        "email": "test@example.com",
        "sub": "auth0|1234567890",
        "role": "user",
        "app_metadata": {},
        "user_metadata": {}
    }

# Mock the chat service
@pytest.fixture
def mock_chat_service():
    with patch('app.routes.chat.chat_service') as mock_service:
        # Create a proper mock response
        mock_response = {
            "message": ChatMessageResponse(
                id="test-msg-123",
                role="assistant",
                content="Mocked response"
            ),
            "conversation_id": "test-convo-123",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            "finish_reason": "stop"
        }
        # Make the chat method an async mock
        mock_service.chat = AsyncMock(return_value=mock_response)
        yield mock_service

# Test the chat endpoint with authentication
@pytest.mark.asyncio
async def test_chat_endpoint_authenticated(authenticated_client, mock_chat_service):
    """Test the chat endpoint with authentication."""
    # When
    with patch("app.routes.chat.get_current_user", new=AsyncMock(return_value=mock_get_current_user())):
        response = authenticated_client.post(
            "/api/chat",
            json=TEST_CHAT_REQUEST
        )
    
    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "conversation_id" in data
    assert data["message"]["role"] == "assistant"
    assert data["message"]["content"] == "Mocked response"
    mock_chat_service.chat.assert_awaited_once()

# Test chat endpoint without authentication
def test_chat_endpoint_unauthenticated(app, client):
    """Test the chat endpoint without authentication."""
    # Clear any authentication overrides for this test
    app.dependency_overrides.clear()
    
    try:
        # When
        response = client.post(
            "/api/chat",
            json=TEST_CHAT_REQUEST
        )
        
        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
            f"Expected 401 for unauthenticated request, got {response.status_code}: {response.text}"
    finally:
        # Make sure to restore overrides after the test
        app.dependency_overrides.clear()

# Test chat endpoint with invalid request
@pytest.mark.asyncio
async def test_chat_endpoint_invalid_request(authenticated_client):
    """Test the chat endpoint with invalid request data."""
    # Given
    invalid_request = {"invalid": "request"}
    
    # When
    with patch("app.routes.chat.get_current_user", new=AsyncMock(return_value=mock_get_current_user())):
        response = authenticated_client.post(
            "/api/chat",
            json=invalid_request
        )
    
    # Then
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "detail" in response.json()
    assert len(response.json()["detail"]) > 0

# Test chat streaming endpoint
@pytest.mark.asyncio
async def test_chat_stream_endpoint(authenticated_client):
    """Test the chat streaming endpoint."""
    # When
    with patch("app.routes.chat.get_current_user", new=AsyncMock(return_value=mock_get_current_user())):
        response = authenticated_client.post(
            "/api/chat/stream",
            json=TEST_CHAT_REQUEST
        )
    
    # Then
    assert response.status_code == status.HTTP_200_OK
    assert "text/event-stream" in response.headers["content-type"]

# Test chat endpoint with invalid persona
@pytest.mark.asyncio
async def test_chat_endpoint_invalid_persona(authenticated_client, mock_chat_service):
    """Test the chat endpoint with an invalid persona."""
    # Given
    invalid_persona_request = TEST_CHAT_REQUEST.copy()
    invalid_persona_request["persona_id"] = "invalid-persona"
    
    # Configure the mock to return a specific response for invalid persona
    mock_chat_service.chat.return_value = {
        "message": ChatMessageResponse(
            id="test-msg-invalid",
            role="assistant",
            content="I'm sorry, I don't recognize that persona."
        ),
        "conversation_id": "test-convo-invalid",
        "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        "finish_reason": "stop"
    }
    
    # When
    with patch("app.routes.chat.get_current_user", new=AsyncMock(return_value=mock_get_current_user())):
        response = authenticated_client.post(
            "/api/chat",
            json=invalid_persona_request
        )
    
    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert data["message"]["role"] == "assistant"
