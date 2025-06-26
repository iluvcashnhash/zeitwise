"""Tests for the LLM Router service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.services.llm_router import LLMRouter, LLMResponse, ProviderConfig, generate

# Test data
TEST_PROMPT = "Hello, how are you?"
TEST_PROFANE_PROMPT = "You're a f***ing idiot!"
TEST_RESPONSE = "I'm fine, thank you!"
TEST_USAGE = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}

# Fixtures
@pytest.fixture
def mock_openai_client():
    with patch('openai.AsyncOpenAI') as mock:
        mock.return_value.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=TEST_RESPONSE))],
            usage=MagicMock(
                prompt_tokens=TEST_USAGE["prompt_tokens"],
                completion_tokens=TEST_USAGE["completion_tokens"],
                total_tokens=TEST_USAGE["total_tokens"],
            )
        )
        yield mock

@pytest.fixture
def mock_grok_client():
    with patch('groq.Groq') as mock:
        mock.return_value.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=TEST_RESPONSE))],
            usage=MagicMock(
                prompt_tokens=TEST_USAGE["prompt_tokens"],
                completion_tokens=TEST_USAGE["completion_tokens"],
                total_tokens=TEST_USAGE["total_tokens"],
            )
        )
        yield mock

@pytest.fixture
def mock_profanity():
    with patch('better_profanity.profanity') as mock:
        mock.contains_profanity.return_value = False
        yield mock

@pytest.fixture
def router_config():
    return {
        "openai": {
            "api_key": "test-openai-key",
            "model": "gpt-4-turbo-preview"
        },
        "xai": {
            "api_key": "test-xai-key",
            "model": "grok-1"
        }
    }

# Tests
class TestLLMRouter:
    """Test the LLM Router service."""
    
    @pytest.mark.asyncio
    async def test_calculate_profanity_score_clean(self, router_config):
        """Test profanity score calculation with clean text."""
        router = LLMRouter()
        score = router.calculate_profanity_score("Hello, how are you?")
        assert 0.0 <= score <= 1.0
        assert score < 0.75  # Below threshold
    
    @pytest.mark.asyncio
    @patch('better_profanity.profanity.contains_profanity', return_value=True)
    async def test_calculate_profanity_score_profane(self, mock_contains):
        """Test profanity score calculation with profane text."""
        router = LLMRouter()
        score = router.calculate_profanity_score("You're a f***ing idiot!")
        assert score > 0.75  # Above threshold
    
    @pytest.mark.asyncio
    async def test_select_provider_openai(self, router_config, mock_openai_client, mock_profanity):
        """Test provider selection for clean text (should use OpenAI)."""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test-key',
            'XAI_API_KEY': 'test-key',
        }):
            router = LLMRouter()
            provider = router.select_provider("Hello, how are you?")
            assert provider == "openai"
    
    @pytest.mark.asyncio
    @patch('better_profanity.profanity.contains_profanity', return_value=True)
    async def test_select_provider_xai(self, mock_contains, router_config, mock_grok_client):
        """Test provider selection for profane text (should use xAI Grok)."""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test-key',
            'XAI_API_KEY': 'test-key',
        }):
            router = LLMRouter()
            provider = router.select_provider("You're a f***ing idiot!")
            assert provider == "xai"
    
    @pytest.mark.asyncio
    async def test_generate_with_openai(self, router_config, mock_openai_client, mock_profanity):
        """Test text generation with OpenAI."""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test-key',
            'XAI_API_KEY': 'test-key',
        }):
            response = await generate("Hello, how are you?")
            assert isinstance(response, LLMResponse)
            assert response.content == TEST_RESPONSE
            assert response.provider == "openai"
            assert response.usage == TEST_USAGE
    
    @pytest.mark.asyncio
    @patch('better_profanity.profanity.contains_profanity', return_value=True)
    async def test_generate_with_xai(self, mock_contains, router_config, mock_grok_client):
        """Test text generation with xAI Grok for profane content."""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test-key',
            'XAI_API_KEY': 'test-key',
        }):
            response = await generate("You're a f***ing idiot!")
            assert isinstance(response, LLMResponse)
            assert response.content == TEST_RESPONSE
            assert response.provider == "xai"
    
    @pytest.mark.asyncio
    async def test_force_provider(self, router_config, mock_openai_client, mock_grok_client):
        """Test forcing a specific provider."""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test-key',
            'XAI_API_KEY': 'test-key',
        }):
            # Force xAI even for clean text
            response = await generate("Hello", provider="xai")
            assert response.provider == "xai"
            
            # Force OpenAI even for profane text
            with patch('better_profanity.profanity.contains_profanity', return_value=True):
                response = await generate("You're a f***ing idiot!", provider="openai")
                assert response.provider == "openai"
    
    @pytest.mark.asyncio
    async def test_generation_parameters(self, router_config, mock_openai_client):
        """Test passing generation parameters."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            response = await generate(
                "Hello, how are you?",
                temperature=0.9,
                max_tokens=100,
                top_p=0.95,
                frequency_penalty=0.5,
                presence_penalty=0.5,
            )
            assert response.provider == "openai"
    
    @pytest.mark.asyncio
    async def test_no_providers_configured(self):
        """Test behavior when no providers are configured."""
        with patch.dict('os.environ', clear=True):
            router = LLMRouter()
            with pytest.raises(ValueError, match="No LLM providers configured"):
                await router.generate("Hello")
    
    @pytest.mark.asyncio
    async def test_only_openai_configured(self, mock_openai_client):
        """Test behavior when only OpenAI is configured."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            router = LLMRouter()
            # Should still work with only one provider
            response = await router.generate("Hello")
            assert response.provider == "openai"
    
    @pytest.mark.asyncio
    async def test_unknown_provider(self, router_config, mock_openai_client):
        """Test behavior when an unknown provider is specified."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with pytest.raises(ValueError, match="Unknown provider"):
                await generate("Hello", provider="unknown")
