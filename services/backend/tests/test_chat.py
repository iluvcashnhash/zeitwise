"""Tests for chat endpoints."""
import pytest
from fastapi import status
from unittest.mock import patch, MagicMock
from app.schemas.requests import Message, MessageRole
from app.schemas.responses import ChatMessageResponse, ChatResponse

# Test data
TEST_MESSAGE = Message(role=MessageRole.USER, content="Hello, world!")
TEST_CHAT_REQUEST = {
    "messages": [{"role": "user", "content": "Hello, world!"}],
    "persona_id": "socrates",
    "temperature": 0.7
}

# Mock the get_current_user dependency
def mock_get_current_user():
    return {"user_id": "test-user", "email": "test@example.com"}

# Mock the chat service
@pytest.fixture
def mock_chat_service():
    with patch('app.routes.chat.chat_service') as mock_service:
        mock_response = ChatMessageResponse(
            role="assistant",
            content="Mocked response"
        )
        mock_service.chat.return_value = {"message": mock_response, "conversation_id": "test-convo"}
        yield mock_service

# Test the chat endpoint with authentication
def test_chat_endpoint_authenticated(authenticated_client, mock_chat_service):
    """Test the chat endpoint with authentication."""
    # When
    with patch("app.routes.chat.get_current_user", new=mock_get_current_user):
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
    mock_chat_service.chat.assert_called_once()

# Test chat endpoint without authentication
def test_chat_endpoint_unauthenticated(client):
    """Test the chat endpoint without authentication."""
    # When
    response = client.post(
        "/api/chat",
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
    with patch("app.routes.chat.get_current_user", new=mock_get_current_user):
        response = authenticated_client.post(
            "/api/chat",
            json=invalid_request
        )
    
    # Then
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# Test chat streaming endpoint
def test_chat_stream_endpoint(authenticated_client):
    """Test the chat streaming endpoint."""
    # When
    with patch("app.routes.chat.get_current_user", new=mock_get_current_user):
        response = authenticated_client.post(
            "/api/chat/stream",
            json=TEST_CHAT_REQUEST
        )
    
    # Then
    assert response.status_code == status.HTTP_200_OK

# Test chat endpoint with invalid persona
def test_chat_endpoint_invalid_persona(authenticated_client):
    """Test the chat endpoint with an invalid persona."""
    # Given
    invalid_persona_request = TEST_CHAT_REQUEST.copy()
    invalid_persona_request["persona_id"] = "invalid-persona"
    
    # When
    with patch("app.routes.chat.get_current_user", new=mock_get_current_user):
        response = authenticated_client.post(
            "/api/chat",
            json=invalid_persona_request
        )
    
    # Then
    assert response.status_code == status.HTTP_200_OK  # Should still return 200 with default response
    data = response.json()
    assert "message" in data
    assert data["message"]["role"] == "assistant"
