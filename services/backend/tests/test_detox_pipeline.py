"""Tests for the detox pipeline."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.detox.pipeline import DetoxPipeline, DetoxAnalysis
from app.models.detox_model import DetoxItem
from app.core.detox_config import detox_settings

# Test data
TEST_HEADLINE = "AI takes over the world, says expert John Doe"
TEST_MASKED_TEXT = "AI takes over the world, says expert [PERSON_1]"
TEST_ENTITIES = [
    {"text": "John Doe", "label": "PERSON", "mask": "[PERSON_1]", "start": 35, "end": 43}
]
TEST_EMBEDDING = [0.1] * 768  # Mock embedding vector
TEST_SIMILAR_ITEMS = [
    {
        "id": "1",
        "score": 0.85,
        "payload": {
            "headline": "Experts warn about AI risks",
            "date": "2023-01-01",
            "source": "Tech News"
        }
    }
]
TEST_ANALYSIS = {
    "analysis": "This is a balanced analysis of the headline.",
    "is_sensational": True,
    "confidence": 0.9,
    "key_points": ["AI is a growing concern", "Experts have mixed opinions"]
}

# Fixtures
@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def detox_pipeline():
    """Detox pipeline instance with mocks."""
    with patch('spacy.load') as mock_spacy_load, \
         patch('sentence_transformers.SentenceTransformer') as mock_embedding_model, \
         patch('qdrant_client.QdrantClient') as mock_qdrant:
        
        # Mock spaCy
        nlp = MagicMock()
        doc = MagicMock()
        doc.ents = [MagicMock(text="John Doe", label_="PERSON", start_char=35, end_char=43)]
        nlp.return_value = doc
        mock_spacy_load.return_value = nlp
        
        # Mock embedding model
        mock_embedding_model.return_value.encode.return_value = TEST_EMBEDDING
        
        # Mock Qdrant client
        mock_qdrant.return_value.search.return_value = [
            MagicMock(
                id=item["id"],
                score=item["score"],
                payload=item["payload"]
            )
            for item in TEST_SIMILAR_ITEMS
        ]
        
        pipeline = DetoxPipeline()
        pipeline.entity_types = ["PERSON"]  # Only test with PERSON entities
        
        yield pipeline

# Tests
class TestDetoxPipeline:
    """Test the detox pipeline."""
    
    @pytest.mark.asyncio
    async def test_mask_entities(self, detox_pipeline):
        """Test entity masking."""
        masked_text, entities = detox_pipeline.mask_entities(TEST_HEADLINE)
        
        assert masked_text == TEST_MASKED_TEXT
        assert len(entities) == 1
        assert entities[0]["text"] == "John Doe"
        assert entities[0]["label"] == "PERSON"
    
    @pytest.mark.asyncio
    async def test_embed_text(self, detox_pipeline):
        """Test text embedding."""
        embedding = detox_pipeline.embed_text("Test text")
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_find_similar_items(self, detox_pipeline):
        """Test finding similar items in Qdrant."""
        similar_items = await detox_pipeline.find_similar_items(
            embedding=TEST_EMBEDDING,
            min_score=0.7,
            limit=5
        )
        
        assert len(similar_items) == len(TEST_SIMILAR_ITEMS)
        assert similar_items[0]["id"] == TEST_SIMILAR_ITEMS[0]["id"]
    
    @pytest.mark.asyncio
    @patch('app.services.detox.pipeline.llm_generate')
    async def test_analyze_with_llm(self, mock_llm_generate, detox_pipeline):
        """Test LLM analysis."""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "analysis": "This is a balanced analysis of the headline.",
            "is_sensational": true,
            "confidence": 0.9,
            "key_points": ["AI is a growing concern", "Experts have mixed opinions"]
        }
        '''
        mock_llm_generate.return_value = mock_response
        
        analysis = await detox_pipeline.analyze_with_llm(
            original_text=TEST_HEADLINE,
            masked_text=TEST_MASKED_TEXT,
            similar_items=TEST_SIMILAR_ITEMS
        )
        
        assert analysis["analysis"] == "This is a balanced analysis of the headline."
        assert analysis["is_sensational"] is True
        assert analysis["confidence"] == 0.9
        assert len(analysis["key_points"]) == 2
    
    @pytest.mark.asyncio
    @patch('app.tasks.meme_generation.generate_meme')
    async def test_generate_meme_if_needed(self, mock_generate_meme, detox_pipeline):
        """Test meme generation trigger."""
        # Mock meme generation
        mock_task = MagicMock()
        mock_task.id = "test-task-id"
        mock_generate_meme.return_value = mock_task
        
        # Test with sensational content
        analysis = {
            "is_sensational": True,
            "analysis": "This is sensational!"
        }
        
        meme_data = await detox_pipeline.generate_meme_if_needed(
            analysis=analysis,
            original_text=TEST_HEADLINE,
            masked_text=TEST_MASKED_TEXT
        )
        
        assert meme_data is not None
        assert meme_data["task_id"] == "test-task-id"
        mock_generate_meme.assert_called_once()
        
        # Test with non-sensational content
        analysis["is_sensational"] = False
        meme_data = await detox_pipeline.generate_meme_if_needed(
            analysis=analysis,
            original_text=TEST_HEADLINE,
            masked_text=TEST_MASKED_TEXT
        )
        
        assert meme_data is None
    
    @pytest.mark.asyncio
    async def test_save_to_detox_items(self, detox_pipeline, mock_db):
        """Test saving detox item to database."""
        # Mock database operations
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        detox_item = await detox_pipeline.save_to_detox_items(
            db=mock_db,
            original_text=TEST_HEADLINE,
            analysis=TEST_ANALYSIS,
            entities=TEST_ENTITIES,
            similar_items=TEST_SIMILAR_ITEMS,
            meme_data={"task_id": "test-task-id", "status": "pending"}
        )
        
        assert detox_item is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()
    
    @pytest.mark.asyncio
    @patch('app.services.detox.pipeline.DetoxPipeline.analyze_with_llm')
    @patch('app.services.detox.pipeline.DetoxPipeline.find_similar_items')
    @patch('app.services.detox.pipeline.DetoxPipeline.mask_entities')
    async def test_process(
        self, 
        mock_mask_entities, 
        mock_find_similar_items, 
        mock_analyze_with_llm,
        detox_pipeline,
        mock_db
    ):
        """Test the full pipeline process."""
        # Setup mocks
        mock_mask_entities.return_value = (TEST_MASKED_TEXT, TEST_ENTITIES)
        mock_find_similar_items.return_value = TEST_SIMILAR_ITEMS
        mock_analyze_with_llm.return_value = TEST_ANALYSIS
        
        # Mock database operations
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock(side_effect=lambda x: setattr(x, 'id', uuid4()))
        
        # Run the pipeline
        result = await detox_pipeline.process(
            text=TEST_HEADLINE,
            db=mock_db,
            generate_meme=True
        )
        
        # Verify results
        assert result["original_text"] == TEST_HEADLINE
        assert result["masked_text"] == TEST_MASKED_TEXT
        assert result["analysis"] == TEST_ANALYSIS
        assert result["similar_items"] == TEST_SIMILAR_ITEMS
        
        # Verify mocks were called
        mock_mask_entities.assert_called_once_with(TEST_HEADLINE)
        mock_find_similar_items.assert_awaited_once()
        mock_analyze_with_llm.assert_awaited_once()
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()
