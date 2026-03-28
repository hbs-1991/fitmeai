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
    CLIENT_ID: str = os.getenv("FATSECRET_CLIENT_ID", "")
    CLIENT_SECRET: str = os.getenv("FATSECRET_CLIENT_SECRET", "")

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
    OAUTH_BASE_URL: str = os.getenv(
        "FATSECRET_OAUTH_BASE_URL", "https://www.fatsecret.com/oauth"
    )

    # Derived URLs
    OAUTH_AUTHORIZE_URL: str = f"{OAUTH_BASE_URL}/authorize"
    OAUTH_TOKEN_URL: str = f"{OAUTH_BASE_URL}/token"

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
