"""Credentials validation and management."""

from typing import Optional, Tuple
from ..config import config
from ..utils import get_logger, ConfigurationError

logger = get_logger(__name__)


def validate_credentials() -> Tuple[bool, Optional[str]]:
    """
    Validate FatSecret API credentials.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not config.CLIENT_ID:
        return False, "FATSECRET_CONSUMER_KEY (or FATSECRET_CLIENT_ID) is not set"

    if not config.CLIENT_SECRET:
        return False, "FATSECRET_CONSUMER_SECRET (or FATSECRET_CLIENT_SECRET) is not set"

    # Basic format validation
    if len(config.CLIENT_ID) < 10:
        return False, "the FatSecret consumer key appears to be invalid (too short)"

    if len(config.CLIENT_SECRET) < 10:
        return False, "the FatSecret consumer secret appears to be invalid (too short)"

    return True, None


def check_credentials() -> None:
    """
    Check credentials and raise exception if invalid.

    Raises:
        ConfigurationError: If credentials are invalid
    """
    is_valid, error_msg = validate_credentials()
    if not is_valid:
        logger.error(f"Credential validation failed: {error_msg}")
        raise ConfigurationError(
            f"Invalid credentials: {error_msg}\n\n"
            "Please ensure you have:\n"
            "1. Created a .env file (copy from .env.example)\n"
            "2. Added FATSECRET_CONSUMER_KEY and FATSECRET_CONSUMER_SECRET\n"
            "   (FATSECRET_CLIENT_ID / FATSECRET_CLIENT_SECRET also work)\n"
            "3. Get credentials from: https://platform.fatsecret.com/api —\n"
            "   the page labels them Consumer Key and Consumer Secret"
        )

    logger.info("Credentials validated successfully")
