"""
FatSecret MCP Server - Public API Only (No Authentication)

This entry point provides access to public FatSecret API features:
- Food search
- Recipe search
- Nutrition information lookup

For food diary, exercise tracking, and weight management, use main.py with OAuth.
"""

from src.fatsecret_mcp.server import create_server
from src.fatsecret_mcp.utils import get_logger, ConfigurationError

logger = get_logger(__name__)


def main():
    """Main entry point for public API server."""
    try:
        logger.info("Starting FatSecret MCP Server (Public API Mode)")
        logger.info("Authentication: Disabled (Client Credentials only)")
        logger.info("Available features: Food search, Recipe search, Nutrition lookup")
        logger.info("For full features, use main.py with OAuth authentication")

        # Create server without user access token
        mcp = create_server(access_token=None, server_name="FatSecret (Public)")

        # Run server
        mcp.run()

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env file and ensure credentials are set")
        raise
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()
