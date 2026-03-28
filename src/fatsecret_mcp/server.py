"""Main FastMCP server for FatSecret Platform API."""

from typing import Optional
from fastmcp import FastMCP

from .config import config
from .api.base_client import FatSecretClient
from .tools.foods_tools import register_food_tools
from .tools.diary_tools import register_diary_tools
from .tools.exercise_tools import register_exercise_tools
from .tools.weight_tools import register_weight_tools
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
            f"Invalid configuration: {error_msg}. "
            "Please set FATSECRET_CLIENT_ID and FATSECRET_CLIENT_SECRET in .env file."
        )

    logger.info(f"Creating {server_name} MCP Server")
    logger.info(f"Authenticated mode: {access_token is not None}")

    # Create MCP server
    mcp = FastMCP(server_name)

    # Create API client
    client = FatSecretClient(access_token=access_token)

    # Register tools
    register_food_tools(mcp, client)

    # Register authenticated tools if we have an access token
    if access_token:
        register_diary_tools(mcp, client)
        register_exercise_tools(mcp, client)
        register_weight_tools(mcp, client)
        logger.info("Registered authenticated tools (diary, exercise, weight)")

    logger.info("FatSecret MCP Server initialized successfully")
    logger.info(f"Available tools: {len(mcp._tool_manager._tools)}")

    return mcp
