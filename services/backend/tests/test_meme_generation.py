"""Tests for the meme generation Celery task."""
import json
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from httpx import Response

from app.tasks.meme_generation import (
    generate_meme_text,
    extract_keywords,
    search_gif,
    store_meme_in_supabase,
    generate_meme
)

# Test data
TEST_HEADLINE = "AI takes over the world"
TEST_ANALYSIS = "Analysis shows AI development is accelerating"
TEST_STYLE = "funny"
TEST_MEME_TEXT = "When you realize you forgot to add the off switch to the AI"
TEST_KEYWORDS = ["realize", "forgot", "switch"]
TEST_GIF_URL = "https://media.giphy.com/media/example.gif"
TEST_PUBLIC_URL = "https://example.supabase.co/storage/v1/object/public/memes/123.json"

# Mock responses
MOCK_OPENAI_RESPONSE = MagicMock()
MOCK_OPENAI_RESPONSE.choices[0].message.content = TEST_MEME_TEXT

MOCK_GIPHY_RESPONSE = {
    "data": [
        {
            "images": {
                "original": {
                    "url": TEST_GIF_URL
                }
            }
        }
    ]
}

MOCK_SUPABASE_INSERT = MagicMock()
MOCK_SUPABASE_INSERT.execute.return_value.data = [{"id": "123"}]

# Tests
class TestMemeGeneration:
    """Test meme generation functionality."""
    
    @pytest.mark.asyncio
    @patch('openai.AsyncOpenAI.chat.completions.create', new_callable=AsyncMock)
    async def test_generate_meme_text(self, mock_openai):
        """Test generating meme text with OpenAI."""
        mock_openai.return_value = MOCK_OPENAI_RESPONSE
        
        result = await generate_meme_text(TEST_HEADLINE, TEST_ANALYSIS, TEST_STYLE)
        
        assert result == TEST_MEME_TEXT
        mock_openai.assert_awaited_once()
    
    def test_extract_keywords(self):
        """Test keyword extraction from text."""
        text = "When you realize you forgot to add the off switch to the AI"
        keywords = extract_keywords(text)
        
        assert len(keywords) == 3
        assert all(isinstance(kw, str) for kw in keywords)
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_search_gif_success(self, mock_get):
        """Test successful GIF search with Giphy API."""
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_GIPHY_RESPONSE
        mock_response.status_code = 200
        mock_get.return_value.__aenter__.return_value = mock_response
        
        gif_url = await search_gif(TEST_KEYWORDS)
        
        assert gif_url == TEST_GIF_URL
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_search_gif_no_results(self, mock_get):
        """Test GIF search with no results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.status_code = 200
        mock_get.return_value.__aenter__.return_value = mock_response
        
        gif_url = await search_gif(["nonexistentkeyword"])
        
        assert gif_url is None
    
    @patch('app.tasks.meme_generation.create_client')
    def test_store_meme_in_supabase(self, mock_supabase):
        """Test storing meme data in Supabase."""
        # Setup mock Supabase client
        mock_supabase.return_value.table.return_value.insert.return_value = MOCK_SUPABASE_INSERT
        mock_supabase.return_value.storage.return_value.from_.return_value.upload.return_value = None
        
        # Call the function
        from app.tasks.meme_generation import get_supabase_client
        supabase = get_supabase_client()
        
        public_url = store_meme_in_supabase(
            supabase=supabase,
            headline=TEST_HEADLINE,
            analysis=TEST_ANALYSIS,
            style=TEST_STYLE,
            meme_text=TEST_MEME_TEXT,
            gif_url=TEST_GIF_URL
        )
        
        # Verify the result
        assert public_url is not None
        assert "supabase.co/storage/v1/object/public/memes/" in public_url
        
        # Verify Supabase was called correctly
        supabase.table.return_value.insert.assert_called_once()
        supabase.storage.return_value.from_.return_value.upload.assert_called_once()
    
    @patch('app.tasks.meme_generation.generate_meme_text', new_callable=AsyncMock)
    @patch('app.tasks.meme_generation.search_gif', new_callable=AsyncMock)
    @patch('app.tasks.meme_generation.store_meme_in_supabase')
    def test_generate_meme_task(self, mock_store, mock_search_gif, mock_gen_text):
        """Test the complete generate_meme Celery task."""
        # Setup mocks
        mock_gen_text.return_value = TEST_MEME_TEXT
        mock_search_gif.return_value = TEST_GIF_URL
        mock_store.return_value = TEST_PUBLIC_URL
        
        # Call the task
        result = generate_meme(TEST_HEADLINE, TEST_ANALYSIS, TEST_STYLE)
        
        # Verify the result
        assert result == {
            "text": TEST_MEME_TEXT,
            "gif_url": TEST_GIF_URL,
            "public_url": TEST_PUBLIC_URL
        }
        
        # Verify mocks were called
        mock_gen_text.assert_awaited_once_with(TEST_HEADLINE, TEST_ANALYSIS, TEST_STYLE)
        mock_search_gif.assert_awaited_once()
        mock_store.assert_called_once()
    
    @patch('app.tasks.meme_generation.generate_meme_text', side_effect=Exception("Test error"))
    def test_generate_meme_task_retry(self, mock_gen_text):
        """Test task retry on error."""
        # Create a mock task request
        task = generate_meme.s(TEST_HEADLINE, TEST_ANALYSIS, TEST_STYLE)
        task.request = MagicMock()
        task.request.retries = 0
        
        # Call the task and verify it raises Retry
        with pytest.raises(generate_meme.retry.exc):
            task.run()
        
        # Verify retry was called
        assert mock_gen_text.called

# Test the async wrapper
@pytest.mark.asyncio
@patch('app.tasks.meme_generation.generate_meme.delay')
async def test_generate_meme_async(mock_delay):
    """Test the async wrapper for the generate_meme task."""
    # Setup mock
    mock_result = MagicMock()
    mock_result.get.return_value = {"status": "success"}
    mock_delay.return_value = mock_result
    
    # Call the async function
    from app.tasks.meme_generation import generate_meme_async
    result = await generate_meme_async(TEST_HEADLINE, TEST_ANALYSIS, TEST_STYLE)
    
    # Verify the result
    assert result == {"status": "success"}
    mock_delay.assert_called_once_with(TEST_HEADLINE, TEST_ANALYSIS, TEST_STYLE)
