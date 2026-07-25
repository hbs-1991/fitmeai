"""Console entry point: `fatsecret-mcp`.

Started as a child process by an MCP client (claude-hermes spawns it via uvx) and
speaks MCP over stdin/stdout. Not a network server: it listens on no port.
"""

from .server import create_server
from .auth import OAuthManager
from .utils import get_logger, AuthenticationError
# create_server raises ConfigurationError; re-exported here so a caller importing the
# entry point can catch it without reaching into .utils.
from .utils import ConfigurationError  # noqa: F401

logger = get_logger(__name__)


def main() -> None:
    logger.info("Starting FatSecret MCP Server (authenticated mode)")
    oauth = OAuthManager()
    access_token = oauth.get_valid_access_token()
    if not access_token:
        raise AuthenticationError(
            "No FatSecret access token. Set FATSECRET_ACCESS_TOKEN and "
            "FATSECRET_ACCESS_SECRET, or run setup_oauth.py on a machine with a browser."
        )
    create_server(access_token=access_token, server_name="FatSecret").run()


if __name__ == "__main__":
    main()
