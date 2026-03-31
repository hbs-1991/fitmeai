"""Configuration management for FatSecret MCP Server."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration settings for FatSecret MCP Server."""

    # FatSecret API Credentials
    # Support both naming conventions: CLIENT_ID/SECRET and CONSUMER_KEY/SECRET
    CLIENT_ID: str = os.getenv("FATSECRET_CLIENT_ID", "") or os.getenv("FATSECRET_CONSUMER_KEY", "")
    CLIENT_SECRET: str = os.getenv("FATSECRET_CLIENT_SECRET", "") or os.getenv("FATSECRET_CONSUMER_SECRET", "")

    # OAuth Configuration
    OAUTH_CALLBACK_URL: str = os.getenv(
        "FATSECRET_OAUTH_CALLBACK_URL", "http://localhost:8080/callback"
    )
    TOKEN_STORAGE: str = os.getenv("FATSECRET_TOKEN_STORAGE", "keyring")

    # Server Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "fatsecret_mcp.log")

    # API Configuration
    API_BASE_URL: str = os.getenv(
        "FATSECRET_API_BASE_URL", "https://platform.fatsecret.com/rest/server.api"
    )

    # OAuth 2.0 (Client Credentials — server-to-server, public API only)
    OAUTH2_TOKEN_URL: str = "https://oauth.fatsecret.com/connect/token"

    # OAuth 1.0 (Three-legged — user-level access for diary/exercise/weight)
    OAUTH1_REQUEST_TOKEN_URL: str = "https://authentication.fatsecret.com/oauth/request_token"
    OAUTH1_AUTHORIZE_URL: str = "https://authentication.fatsecret.com/oauth/authorize"
    OAUTH1_ACCESS_TOKEN_URL: str = "https://authentication.fatsecret.com/oauth/access_token"

    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """
        Validate configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not cls.CLIENT_ID:
            return False, "FATSECRET_CLIENT_ID is not set"
        if not cls.CLIENT_SECRET:
            return False, "FATSECRET_CLIENT_SECRET is not set"
        return True, None

    @classmethod
    def is_configured(cls) -> bool:
        """Check if minimum configuration is present."""
        return bool(cls.CLIENT_ID and cls.CLIENT_SECRET)


# Global config instance
config = Config()
