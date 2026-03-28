"""
OAuth Setup Utility for FatSecret MCP Server

This script guides you through the OAuth authorization process to enable
authenticated features like food diary, exercise tracking, and weight management.

Run this once to authorize the application and store tokens.
"""

import sys
from src.fatsecret_mcp.auth.oauth_manager import run_oauth_flow
from src.fatsecret_mcp.auth.credentials import check_credentials
from src.fatsecret_mcp.utils import get_logger, ConfigurationError

logger = get_logger(__name__)


def main():
    """Main entry point for OAuth setup."""
    print("\n" + "=" * 60)
    print("FatSecret MCP Server - OAuth Setup")
    print("=" * 60)
    print("\nThis will authorize the application to access your FatSecret account.")
    print("\nFeatures enabled after authorization:")
    print("  • Food diary tracking")
    print("  • Exercise logging")
    print("  • Weight management")
    print("  • Saved meals")
    print("  • Favorites")

    # Validate credentials
    try:
        check_credentials()
    except ConfigurationError as e:
        print(f"\n❌ Configuration Error:\n{e}")
        print("\nPlease fix the configuration and try again.")
        sys.exit(1)

    print("\n" + "-" * 60)
    input("Press ENTER to continue with authorization...")

    # Run OAuth flow
    try:
        success = run_oauth_flow()

        if success:
            print("\n" + "=" * 60)
            print("Setup Complete!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Run the authenticated server: python main.py")
            print("2. Configure Claude Desktop to use the server")
            print("3. Start tracking your nutrition and exercise!")
            print("\nSee docs/setup.md for Claude Desktop configuration.")
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("Setup Failed")
            print("=" * 60)
            print("\nPlease try again. If the problem persists, check:")
            print("• Your internet connection")
            print("• Your FatSecret API credentials")
            print("• The callback URL (should be http://localhost:8080/callback)")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during OAuth setup: {e}")
        print(f"\n❌ Unexpected error: {e}")
        print("\nPlease report this issue with the error details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
