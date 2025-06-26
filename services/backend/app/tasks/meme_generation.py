"""Meme generation tasks using Celery."""
import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus

import httpx
import openai
from celery import shared_task
from openai import AsyncOpenAI
from supabase import create_client, Client as SupabaseClient

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Initialize Supabase client
def get_supabase_client() -> SupabaseClient:
    """Initialize and return a Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

async def generate_meme_text(headline: str, analysis: str, style: str) -> str:
    """
    Generate witty meme text using GPT-3.5.
    
    Args:
        headline: The headline to create a meme for
        analysis: Analysis of the headline
        style: Style/tone for the meme
        
    Returns:
        Generated meme text (1-2 lines)
    """
    prompt = f"""Create a concise, witty meme text (1-2 lines) based on this information:
    
    Headline: {headline}
    Analysis: {analysis}
    Style: {style}
    
    Keep it funny, relevant, and under 100 characters."""
    
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative meme writer. Create funny, witty, and engaging meme text."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.8,
        )
        
        meme_text = response.choices[0].message.content.strip()
        # Clean up any quotes or newlines
        meme_text = meme_text.replace('"', '').replace('\n', ' ').strip()
        return meme_text
    except Exception as e:
        logger.error(f"Error generating meme text: {e}")
        raise

def extract_keywords(text: str, num_keywords: int = 3) -> List[str]:
    """
    Extract keywords from text using simple heuristics.
    
    Args:
        text: Input text
        num_keywords: Number of keywords to extract
        
    Returns:
        List of keywords
    """
    # Remove common words and special characters
    stop_words = {"the", "and", "or", "in", "on", "at", "to", "for", "a", "an", "is", "are", "was", "were"}
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Count word frequencies
    word_freq = {}
    for word in words:
        if word not in stop_words and len(word) > 2:  # Ignore very short words
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top N
    keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:num_keywords]
    return [kw[0] for kw in keywords]

async def search_gif(keywords: List[str]) -> Optional[str]:
    """
    Search for a GIF using Giphy API.
    
    Args:
        keywords: List of keywords to search for
        
    Returns:
        URL of the GIF or None if not found
    """
    if not settings.GIPHY_API_KEY:
        logger.error("GIPHY_API_KEY not configured")
        return None
    
    query = " ".join(keywords)
    url = f"https://api.giphy.com/v1/gifs/search?api_key={settings.GIPHY_API_KEY}&q={quote_plus(query)}&limit=1&rating=pg-13"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("data") and len(data["data"]) > 0:
                return data["data"][0]["images"]["original"]["url"]
            return None
    except Exception as e:
        logger.error(f"Error searching Giphy: {e}")
        return None

def store_meme_in_supabase(
    supabase: SupabaseClient,
    headline: str,
    analysis: str,
    style: str,
    meme_text: str,
    gif_url: str
) -> str:
    """
    Store meme data in Supabase.
    
    Args:
        supabase: Supabase client
        headline: Original headline
        analysis: Analysis text
        style: Style/tone
        meme_text: Generated meme text
        gif_url: URL of the GIF
        
    Returns:
        Public URL of the stored meme
    """
    try:
        # Insert into memes table
        result = supabase.table("memes").insert({
            "headline": headline,
            "analysis": analysis,
            "style": style,
            "text": meme_text,
            "gif_url": gif_url
        }).execute()
        
        # Get the inserted record
        meme_id = result.data[0]["id"]
        
        # Generate public URL
        public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/memes/{meme_id}.json"
        
        # Store the full data in storage
        meme_data = {
            "headline": headline,
            "analysis": analysis,
            "style": style,
            "text": meme_text,
            "gif_url": gif_url,
            "public_url": public_url
        }
        
        # Upload to storage
        supabase.storage().from_("memes").upload(
            f"{meme_id}.json",
            json.dumps(meme_data),
            {"content-type": "application/json"}
        )
        
        return public_url
        
    except Exception as e:
        logger.error(f"Error storing meme in Supabase: {e}")
        raise

@shared_task(bind=True, max_retries=3, default_retry_delay=60, queue="memes")
def generate_meme(self, headline: str, analysis: str, style: str) -> Dict[str, str]:
    """
    Celery task to generate a meme.
    
    Args:
        headline: The headline to create a meme for
        analysis: Analysis of the headline
        style: Style/tone for the meme
        
    Returns:
        Dict containing the meme data and public URL
    """
    try:
        # Generate meme text
        meme_text = generate_meme_text(headline, analysis, style)
        
        # Extract keywords
        keywords = extract_keywords(f"{headline} {analysis} {meme_text}")
        
        # Search for GIF
        gif_url = search_gif(keywords)
        
        # Store in Supabase
        supabase = get_supabase_client()
        public_url = store_meme_in_supabase(
            supabase=supabase,
            headline=headline,
            analysis=analysis,
            style=style,
            meme_text=meme_text,
            gif_url=gif_url or ""
        )
        
        return {
            "text": meme_text,
            "gif_url": gif_url,
            "public_url": public_url
        }
        
    except Exception as exc:
        logger.error(f"Error in generate_meme task: {exc}")
        # Retry the task with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retry))

# Async version of the task for use in FastAPI endpoints
async def generate_meme_async(headline: str, analysis: str, style: str) -> Dict[str, str]:
    """
    Async wrapper for the generate_meme task.
    
    Args:
        headline: The headline to create a meme for
        analysis: Analysis of the headline
        style: Style/tone for the meme
        
    Returns:
        Dict containing the meme data and public URL
    """
    # In a real implementation, this would use Celery's async task calling
    # For now, we'll just call the sync version directly
    return generate_meme.delay(headline, analysis, style).get()
