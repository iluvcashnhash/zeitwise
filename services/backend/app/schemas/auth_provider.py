"""Authentication provider schemas and enums."""
from enum import Enum
from typing import Dict, Optional

class AuthProvider(str, Enum):
    """Enumeration of supported authentication providers."""
    EMAIL = "email"  # Email/password authentication
    GOOGLE = "google"  # Google OAuth
    GITHUB = "github"  # GitHub OAuth
    APPLE = "apple"  # Apple Sign In
    FACEBOOK = "facebook"  # Facebook OAuth
    TWITTER = "twitter"  # Twitter OAuth
    MICROSOFT = "microsoft"  # Microsoft OAuth
    DISCORD = "discord"  # Discord OAuth
    PHONE = "phone"  # Phone number authentication
    MAGIC_LINK = "magic_link"  # Magic link authentication
    
    @classmethod
    def from_string(cls, provider: str) -> 'AuthProvider':
        """Convert a string to an AuthProvider enum value."""
        provider = provider.lower()
        for p in cls:
            if p.value == provider:
                return p
        raise ValueError(f"Unknown provider: {provider}")

# Map provider strings to AuthProvider enum
PROVIDER_MAP: Dict[str, AuthProvider] = {
    "email": AuthProvider.EMAIL,
    "google": AuthProvider.GOOGLE,
    "github": AuthProvider.GITHUB,
    "apple": AuthProvider.APPLE,
    "facebook": AuthProvider.FACEBOOK,
    "twitter": AuthProvider.TWITTER,
    "microsoft": AuthProvider.MICROSOFT,
    "discord": AuthProvider.DISCORD,
    "phone": AuthProvider.PHONE,
    "magic_link": AuthProvider.MAGIC_LINK,
}

def get_auth_provider(provider_str: str) -> Optional[AuthProvider]:
    """Get the AuthProvider enum for a provider string."""
    return PROVIDER_MAP.get(provider_str.lower())

def is_social_provider(provider: AuthProvider) -> bool:
    """Check if a provider is a social provider (OAuth)."""
    return provider in [
        AuthProvider.GOOGLE,
        AuthProvider.GITHUB,
        AuthProvider.APPLE,
        AuthProvider.FACEBOOK,
        AuthProvider.TWITTER,
        AuthProvider.MICROSOFT,
        AuthProvider.DISCORD,
    ]

def is_email_provider(provider: AuthProvider) -> bool:
    """Check if a provider is an email-based provider."""
    return provider in [AuthProvider.EMAIL, AuthProvider.MAGIC_LINK]

def is_phone_provider(provider: AuthProvider) -> bool:
    """Check if a provider is a phone-based provider."""
    return provider == AuthProvider.PHONE
