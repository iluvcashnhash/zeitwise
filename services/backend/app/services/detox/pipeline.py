"""
Detox Pipeline

Processes news headlines through a detoxification pipeline:
1. Mask entities using spaCy
2. Embed and search for similar historical news using Qdrant
3. Generate calm analysis using LLM
4. Optionally trigger meme generation
5. Persist results to detox_items
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json
import re

import spacy
from spacy.tokens import Doc, Span
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchText
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.llm_router import generate as llm_generate
from app.tasks.meme_generation import generate_meme
from app.db.deps import get_db
from app.models.detox_model import DetoxItem

# Configure logging
logger = logging.getLogger(__name__)

# Load models and clients
nlp = spacy.load("en_core_web_sm")
embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL or "sentence-transformers/all-mpnet-base-v2")
qdrant_client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)

class DetoxAnalysis(BaseModel):
    """Model for detox analysis results."""
    original_text: str = Field(..., description="Original headline text")
    masked_text: str = Field(..., description="Text with entities masked")
    entities: List[Dict[str, str]] = Field(default_factory=list, description="List of detected entities")
    similar_items: List[Dict[str, Any]] = Field(default_factory=list, description="Similar historical items")
    analysis: str = Field(..., description="LLM-generated analysis")
    is_sensational: bool = Field(False, description="Whether the content is considered sensational")
    confidence: float = Field(0.0, description="Confidence score (0-1)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class DetoxPipeline:
    """Pipeline for detoxifying and analyzing news content."""
    
    def __init__(self):
        """Initialize the detox pipeline."""
        self.entity_types = ["PERSON", "ORG", "GPE", "LOC", "PRODUCT", "EVENT", "WORK_OF_ART"]
        self.similarity_threshold = 0.8
        self.max_similar_items = 3
    
    def mask_entities(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Mask named entities in the text.
        
        Args:
            text: Input text to process
            
        Returns:
            Tuple of (masked_text, entities)
        """
        doc = nlp(text)
        masked_text = text
        entities = []
        
        # Sort entities by start position in reverse to avoid offset issues
        sorted_entities = sorted(doc.ents, key=lambda e: e.start_char, reverse=True)
        
        for ent in sorted_entities:
            if ent.label_ in self.entity_types:
                # Create a mask like [PERSON_1], [ORG_2], etc.
                mask = f"[{ent.label_}_{len(entities) + 1}]"
                masked_text = (
                    masked_text[:ent.start_char] + 
                    mask + 
                    masked_text[ent.end_char:]
                )
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "mask": mask,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
        
        return masked_text, entities
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding vector for the given text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding
        """
        # For long texts, we might want to chunk or truncate
        if len(text) > 512:  # Typical max length for many models
            text = text[:512]
            
        embedding = embedding_model.encode([text], show_progress_bar=False)[0]
        return embedding.tolist()
    
    async def find_similar_items(
        self, 
        embedding: List[float], 
        min_score: float = 0.7,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar items in Qdrant vector store.
        
        Args:
            embedding: Query embedding vector
            min_score: Minimum similarity score (0-1)
            limit: Maximum number of results to return
            
        Returns:
            List of similar items with scores
        """
        try:
            search_results = qdrant_client.search(
                collection_name=settings.QDRANT_COLLECTION,
                query_vector=embedding,
                limit=limit,
                score_threshold=min_score
            )
            
            return [
                {
                    "id": str(hit.id),
                    "score": hit.score,
                    "payload": hit.payload or {}
                }
                for hit in search_results
            ]
        except Exception as e:
            logger.error(f"Error searching Qdrant: {e}")
            return []
    
    async def analyze_with_llm(
        self,
        original_text: str,
        masked_text: str,
        similar_items: List[Dict[str, Any]],
        style: str = "calm, analytical"
    ) -> Dict[str, Any]:
        """
        Generate a calm analysis of the content using LLM.
        
        Args:
            original_text: Original headline
            masked_text: Headline with entities masked
            similar_items: List of similar historical items
            style: Desired style/tone for the analysis
            
        Returns:
            Dict containing analysis results
        """
        # Prepare context from similar items
        context = "\n".join([
            f"- {item['payload'].get('headline', '')} ({item['score']:.2f})"
            for item in similar_items[:3]  # Use top 3 similar items
        ]) or "No similar historical items found."
        
        prompt = f"""You are a news analysis assistant. Provide a calm, balanced analysis of this headline.
        
Original headline: {original_text}
Masked version: {masked_text}

Similar historical headlines:
{context}

Please provide:
1. A brief analysis of the headline's content
2. Historical context if available
3. A balanced perspective
4. A confidence score (0-1) on whether this is sensationalized

Format your response as JSON with these fields:
- "analysis": "your analysis here"
- "is_sensational": boolean
- "confidence": 0.0 to 1.0
- "key_points": ["point 1", "point 2", ...]
"""
        
        try:
            response = await llm_generate(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for more focused output
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            result = json.loads(response.content)
            return {
                "analysis": result.get("analysis", ""),
                "is_sensational": result.get("is_sensational", False),
                "confidence": float(result.get("confidence", 0.5)),
                "key_points": result.get("key_points", [])
            }
            
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return {
                "analysis": "Unable to generate analysis due to an error.",
                "is_sensational": False,
                "confidence": 0.0,
                "key_points": []
            }
    
    async def generate_meme_if_needed(
        self,
        analysis: Dict[str, Any],
        original_text: str,
        masked_text: str
    ) -> Optional[Dict[str, Any]]:
        """
        Trigger meme generation if the content is sensational.
        
        Args:
            analysis: Analysis results from analyze_with_llm
            original_text: Original headline
            masked_text: Masked headline
            
        Returns:
            Meme data if generated, None otherwise
        """
        if not analysis.get("is_sensational", False):
            return None
            
        try:
            # Create a prompt for the meme
            meme_prompt = f"""Create a meme about this sensational headline:
            
Original: {original_text}
Masked: {masked_text}

Analysis: {analysis.get('analysis', '')}

Make it funny but not offensive."""
            
            # Trigger the Celery task
            task = generate_meme.delay(
                headline=original_text,
                analysis=analysis.get("analysis", ""),
                style="funny, satirical"
            )
            
            return {
                "task_id": task.id,
                "status": "pending"
            }
        except Exception as e:
            logger.error(f"Error triggering meme generation: {e}")
            return None
    
    async def save_to_detox_items(
        self,
        db: Any,
        original_text: str,
        analysis: Dict[str, Any],
        entities: List[Dict[str, str]],
        similar_items: List[Dict[str, Any]],
        meme_data: Optional[Dict[str, Any]] = None
    ) -> DetoxItem:
        """
        Save the analysis results to the database.
        
        Args:
            db: Database session
            original_text: Original headline
            analysis: Analysis results
            entities: List of detected entities
            similar_items: Similar historical items
            meme_data: Meme generation data if applicable
            
        Returns:
            The created DetoxItem
        """
        try:
            detox_item = DetoxItem(
                original_text=original_text,
                analysis=analysis.get("analysis", ""),
                is_sensational=analysis.get("is_sensational", False),
                confidence=analysis.get("confidence", 0.0),
                entities=entities,
                similar_items=similar_items,
                meme_task_id=meme_data.get("task_id") if meme_data else None,
                metadata={
                    "key_points": analysis.get("key_points", []),
                    "meme_status": meme_data.get("status") if meme_data else None
                }
            )
            
            db.add(detox_item)
            await db.commit()
            await db.refresh(detox_item)
            
            return detox_item
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error saving to detox_items: {e}")
            raise
    
    async def process(
        self,
        text: str,
        db: Any = None,
        generate_meme: bool = True
    ) -> Dict[str, Any]:
        """
        Process a text through the detox pipeline.
        
        Args:
            text: Input text to process
            db: Optional database session
            generate_meme: Whether to generate a meme if content is sensational
            
        Returns:
            Dict containing all processing results
        """
        if not text.strip():
            raise ValueError("Input text cannot be empty")
        
        # 1. Mask entities
        masked_text, entities = self.mask_entities(text)
        
        # 2. Generate embedding and find similar items
        embedding = self.embed_text(masked_text)
        similar_items = await self.find_similar_items(
            embedding=embedding,
            min_score=self.similarity_threshold,
            limit=self.max_similar_items
        )
        
        # 3. Analyze with LLM
        analysis = await self.analyze_with_llm(
            original_text=text,
            masked_text=masked_text,
            similar_items=similar_items
        )
        
        # 4. Generate meme if needed
        meme_data = None
        if generate_meme and analysis.get("is_sensational", False):
            meme_data = await self.generate_meme_if_needed(
                analysis=analysis,
                original_text=text,
                masked_text=masked_text
            )
        
        # 5. Save to database if session provided
        detox_item = None
        if db:
            detox_item = await self.save_to_detox_items(
                db=db,
                original_text=text,
                analysis=analysis,
                entities=entities,
                similar_items=similar_items,
                meme_data=meme_data or {}
            )
        
        return {
            "original_text": text,
            "masked_text": masked_text,
            "entities": entities,
            "similar_items": similar_items,
            "analysis": analysis,
            "meme_data": meme_data,
            "detox_item_id": str(detox_item.id) if detox_item else None
        }

# Create a singleton instance
detox_pipeline = DetoxPipeline()
