"""
LLM Router Service

Routes prompts between different AI providers based on content analysis.
Uses profanity score to determine which model to use for generation.
"""
import logging
from typing import Dict, Any, Optional, Union

from better_profanity import profanity
import openai
from groq import Groq
from pydantic import BaseModel, Field, validator
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class ProviderConfig(BaseModel):
    """Configuration for an LLM provider."""
    name: str
    client: Any
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[list] = None

class LLMResponse(BaseModel):
    """Standardized response from LLM generation."""
    content: str
    provider: str
    model: str
    usage: Dict[str, int] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class LLMRouter:
    """
    Routes prompts between different AI providers based on content analysis.
    
    By default, uses profanity score to determine which model to use:
    - If profanity score > 0.75: Uses xAI Grok
    - Otherwise: Uses OpenAI GPT-4
    """
    
    def __init__(self):
        """Initialize the LLM router with configured providers."""
        self.providers = self._initialize_providers()
        self.default_provider = "openai"
        self.profanity_threshold = 0.75
        
        # Initialize profanity filter
        profanity.load_censor_words()
    
    def _initialize_providers(self) -> Dict[str, ProviderConfig]:
        """Initialize and configure available LLM providers."""
        providers = {}
        
        # Configure OpenAI
        if settings.OPENAI_API_KEY:
            openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            providers["openai"] = ProviderConfig(
                name="openai",
                client=openai_client,
                model=settings.OPENAI_MODEL or "gpt-4-turbo-preview",
                temperature=0.7,
                max_tokens=2048,
            )
        
        # Configure xAI Grok
        if settings.XAI_API_KEY:
            groq_client = Groq(api_key=settings.XAI_API_KEY)
            providers["xai"] = ProviderConfig(
                name="xai",
                client=groq_client,
                model=settings.XAI_MODEL or "grok-1",
                temperature=0.9,  # Slightly more creative for handling profane content
                max_tokens=2048,
            )
        
        return providers
    
    def calculate_profanity_score(self, text: str) -> float:
        """
        Calculate a profanity score for the given text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            float: Profanity score between 0.0 (no profanity) and 1.0 (high profanity)
        """
        if not text.strip():
            return 0.0
            
        # Calculate basic profanity metrics
        words = text.split()
        if not words:
            return 0.0
            
        # Check for profanity
        has_profanity = profanity.contains_profanity(text)
        
        # Simple heuristic: if profanity is detected, return a score above threshold
        if has_profanity:
            return 0.8  # Above threshold to trigger xAI Grok
            
        return 0.1  # Below threshold for OpenAI
    
    def select_provider(self, prompt: str) -> str:
        """
        Select the appropriate provider based on the prompt content.
        
        Args:
            prompt: The input prompt to analyze
            
        Returns:
            str: The selected provider name
        """
        if not self.providers:
            raise ValueError("No LLM providers configured")
            
        # If only one provider is available, use it
        if len(self.providers) == 1:
            return next(iter(self.providers.keys()))
        
        # Calculate profanity score
        profanity_score = self.calculate_profanity_score(prompt)
        
        # Log the routing decision
        logger.info(f"Profanity score: {profanity_score:.2f} for prompt: {prompt[:100]}...")
        
        # Route based on profanity score
        if profanity_score > self.profanity_threshold and "xai" in self.providers:
            return "xai"
        
        return self.default_provider
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        provider: Optional[str] = None,
        **generation_kwargs,
    ) -> LLMResponse:
        """
        Generate text using the appropriate LLM provider.
        
        Args:
            prompt: The input prompt
            provider: Optional provider name to force a specific provider
            **generation_kwargs: Additional generation parameters
            
        Returns:
            LLMResponse: The generated response and metadata
            
        Raises:
            ValueError: If no providers are configured or generation fails
        """
        if not self.providers:
            raise ValueError("No LLM providers configured")
        
        # Select provider if not specified
        if not provider:
            provider = self.select_provider(prompt)
        
        if provider not in self.providers:
            raise ValueError(f"Unknown provider: {provider}")
        
        config = self.providers[provider]
        
        try:
            # Prepare generation parameters
            params = {
                "model": config.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "top_p": config.top_p,
                "frequency_penalty": config.frequency_penalty,
                "presence_penalty": config.presence_penalty,
            }
            
            # Apply any overrides from kwargs
            params.update(generation_kwargs)
            
            logger.info(f"Generating with {provider} (model: {config.model})")
            
            # Call the appropriate provider
            if provider == "openai":
                response = await config.client.chat.completions.create(**params)
                content = response.choices[0].message.content
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            elif provider == "xai":
                response = config.client.chat.completions.create(**params)
                content = response.choices[0].message.content
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            return LLMResponse(
                content=content,
                provider=provider,
                model=config.model,
                usage=usage,
                metadata={"profanity_score": self.calculate_profanity_score(prompt)},
            )
            
        except Exception as e:
            logger.error(f"Error generating with {provider}: {str(e)}", exc_info=True)
            raise

# Create a singleton instance
llm_router = LLMRouter()

# Public async interface
async def generate(prompt: str, **kwargs) -> LLMResponse:
    """
    Generate text using the LLM router.
    
    Args:
        prompt: The input prompt
        **kwargs: Additional generation parameters
        
    Returns:
        LLMResponse: The generated response and metadata
    """
    return await llm_router.generate(prompt, **kwargs)
