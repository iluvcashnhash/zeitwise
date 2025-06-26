"""Tests for chat endpoints."""
import pytest
from fastapi import status
from unittest.mock import patch, MagicMock, AsyncMock
from app.schemas.requests import Message, MessageRole
from app.schemas.responses import ChatMessageResponse, ChatResponse

# Test data
TEST_MESSAGE = Message(role=MessageRole.USER, content="Hello, world!")
TEST_CHAT_REQUEST = {
    "messages": [{"role": "user", "content": "Hello, world!"}],
    "persona_id": "socrates",
    "temperature": 0.7
}

# Test the chat endpoint with authentication
@patch("app.routes.chat.uuid.uuid4")
async def test_chat_endpoint_authenticated(mock_uuid, authenticated_client):
    """Test the chat endpoint with authentication."""
    # Given
    mock_uuid.return_value = "test-conversation-id"
    
    # When
    response = authenticated_client.post(
        "/api/v1/chat",
        json=TEST_CHAT_REQUEST
    )
    
    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "conversation_id" in data
    assert data["conversation_id"] == "test-conversation-id"
    assert data["message"]["role"] == "assistant"
    assert "You said: Hello, world!" in data["message"]["content"]

# Test chat endpoint without authentication
def test_chat_endpoint_unauthenticated(client):
    """Test the chat endpoint without authentication."""
    # When
    response = client.post(
        "/api/v1/chat",
        json=TEST_CHAT_REQUEST
    )
    
    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# Test chat endpoint with invalid request
def test_chat_endpoint_invalid_request(authenticated_client):
    """Test the chat endpoint with invalid request data."""
    # Given
    invalid_request = {"invalid": "request"}
    
    # When
    response = authenticated_client.post(
        "/api/v1/chat",
        json=invalid_request
    )
    
    # Then
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# Test chat streaming endpoint
@patch("app.routes.chat.StreamingResponse")
async def test_chat_stream_endpoint(mock_streaming_response, authenticated_client):
    """Test the chat streaming endpoint."""
    # Given
    mock_response = MagicMock()
    mock_streaming_response.return_value = mock_response
    
    # When
    response = authenticated_client.post(
        "/api/v1/chat/stream",
        json=TEST_CHAT_REQUEST
    )
    
    # Then
    assert response.status_code == status.HTTP_200_OK
    mock_streaming_response.assert_called_once()

# Test chat endpoint with invalid persona
def test_chat_endpoint_invalid_persona(authenticated_client):
    """Test the chat endpoint with an invalid persona."""
    # Given
    invalid_persona_request = TEST_CHAT_REQUEST.copy()
    invalid_persona_request["persona_id"] = "invalid-persona"
    
    # When
    response = authenticated_client.post(
        "/api/v1/chat",
        json=invalid_persona_request
    )
    
    # Then
    assert response.status_code == status.HTTP_200_OK  # Should still return 200, but with a default response
    assert "message" in response.json()
