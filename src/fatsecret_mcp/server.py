"""Main FastMCP server for FatSecret Platform API."""

from typing import Optional
from fastmcp import FastMCP

from .config import config
from .api.base_client import FatSecretClient
from .tools.food import register_food_tool
from .tools.diary import register_diary_tool
from .tools.exercise import register_exercise_tool
from .tools.weight import register_weight_tool
from .utils import setup_logging, get_logger, ConfigurationError

# Setup logging
setup_logging()
logger = get_logger(__name__)


def create_server(
    access_token: Optional[str] = None, server_name: str = "FatSecret"
) -> FastMCP:
    """
    Create and configure FastMCP server.

    Args:
        access_token: Optional OAuth access token for authenticated operations
        server_name: Name of the MCP server

    Returns:
        Configured FastMCP server instance

    Raises:
        ConfigurationError: If configuration is invalid
    """
    # Validate configuration
    is_valid, error_msg = config.validate()
    if not is_valid:
        raise ConfigurationError(
            f"Invalid configuration: {error_msg}. Set the application credentials "
            "from https://platform.fatsecret.com/api — the page labels them Consumer "
            "Key and Consumer Secret (FATSECRET_CONSUMER_KEY / "
            "FATSECRET_CONSUMER_SECRET; FATSECRET_CLIENT_ID / FATSECRET_CLIENT_SECRET "
            "are accepted as aliases)."
        )

    logger.info(f"Creating {server_name} MCP Server")
    logger.info(f"Authenticated mode: {access_token is not None}")

    # Create MCP server
    mcp = FastMCP(server_name)

    # Create API client
    client = FatSecretClient(access_token=access_token)

    # Food lookup works on the app credentials alone; the diary, exercise and weight
    # tools need a user access token, so they are only registered when one is present.
    register_food_tool(mcp, client)
    if access_token:
        register_diary_tool(mcp, client)
        register_exercise_tool(mcp, client)
        register_weight_tool(mcp, client)
        logger.info("Registered authenticated tools (diary, exercise, weight)")

    logger.info("FatSecret MCP Server initialized successfully")

    return mcp
