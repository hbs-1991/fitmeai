"""
FatSecret MCP Server - Full Features (Authenticated)

This entry point provides access to all FatSecret API features including:
- Food search and nutrition lookup
- Food diary tracking
- Exercise tracking
- Weight management
- Saved meals
- Favorites

Requires OAuth authentication. Run setup_oauth.py first if not already done.
"""

from src.fatsecret_mcp.server import create_server
from src.fatsecret_mcp.auth import OAuthManager
from src.fatsecret_mcp.utils import get_logger, ConfigurationError, AuthenticationError

logger = get_logger(__name__)


def main():
    """Main entry point for authenticated server."""
    try:
        logger.info("Starting FatSecret MCP Server (Authenticated Mode)")

        # Get OAuth manager
        oauth = OAuthManager()

        # Get valid access token
        logger.info("Retrieving access token from Windows Credential Manager")
        access_token = oauth.get_valid_access_token()

        if not access_token:
            logger.error("No valid access token found")
            print("\n" + "=" * 60)
            print("Authentication Required")
            print("=" * 60)
            print("\nNo valid OAuth token found.")
            print("\nPlease run the OAuth setup first:")
            print("  python setup_oauth.py")
            print("\nThis will authorize the application and store your credentials.")
            raise AuthenticationError(
                "No valid access token. Please run setup_oauth.py first."
            )

        logger.info("Access token retrieved successfully")
        logger.info("Authentication: Enabled (User Access Token)")
        logger.info("Available features: Food search, Diary, Exercise, Weight, Meals")

        # Create server with user access token
        mcp = create_server(access_token=access_token, server_name="FatSecret")

        # Run server
        mcp.run()

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env file and ensure credentials are set")
        raise
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()
