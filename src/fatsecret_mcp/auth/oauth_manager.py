"""OAuth 2.0 authentication manager for FatSecret API."""

import time
import keyring
import secrets
import webbrowser
from base64 import b64encode
from datetime import datetime, timedelta
from typing import Optional, Tuple
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse
import requests

from ..config import config
from ..utils import get_logger, AuthenticationError, TokenError

logger = get_logger(__name__)


class OAuthManager:
    """Manages OAuth 2.0 authentication flow and token storage."""

    SERVICE_NAME = "fatsecret_mcp"
    TOKEN_KEYS = {
        "access_token": "access_token",
        "refresh_token": "refresh_token",
        "token_expiry": "token_expiry",
    }

    def __init__(self):
        """Initialize OAuth Manager."""
        self.client_id = config.CLIENT_ID
        self.client_secret = config.CLIENT_SECRET
        self.callback_url = config.OAUTH_CALLBACK_URL
        self.authorize_url = config.OAUTH_AUTHORIZE_URL
        self.token_url = config.OAUTH_TOKEN_URL

    def store_tokens(
        self, access_token: str, refresh_token: str, expires_in: int
    ) -> None:
        """
        Store OAuth tokens in Windows Credential Manager.

        Args:
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_in: Token lifetime in seconds
        """
        try:
            # Calculate expiry time
            expiry = datetime.now() + timedelta(seconds=expires_in)
            expiry_str = expiry.isoformat()

            # Store in keyring
            keyring.set_password(
                self.SERVICE_NAME, self.TOKEN_KEYS["access_token"], access_token
            )
            keyring.set_password(
                self.SERVICE_NAME, self.TOKEN_KEYS["refresh_token"], refresh_token
            )
            keyring.set_password(
                self.SERVICE_NAME, self.TOKEN_KEYS["token_expiry"], expiry_str
            )

            logger.info("Tokens stored successfully in Windows Credential Manager")

        except Exception as e:
            logger.error(f"Failed to store tokens: {e}")
            raise TokenError(f"Failed to store tokens: {e}")

    def get_stored_tokens(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Retrieve stored tokens from Windows Credential Manager.

        Returns:
            Tuple of (access_token, refresh_token, expiry_time)
        """
        try:
            access_token = keyring.get_password(
                self.SERVICE_NAME, self.TOKEN_KEYS["access_token"]
            )
            refresh_token = keyring.get_password(
                self.SERVICE_NAME, self.TOKEN_KEYS["refresh_token"]
            )
            expiry_str = keyring.get_password(
                self.SERVICE_NAME, self.TOKEN_KEYS["token_expiry"]
            )

            return access_token, refresh_token, expiry_str

        except Exception as e:
            logger.error(f"Failed to retrieve tokens: {e}")
            return None, None, None

    def clear_tokens(self) -> None:
        """Clear stored tokens from Windows Credential Manager."""
        try:
            for key in self.TOKEN_KEYS.values():
                try:
                    keyring.delete_password(self.SERVICE_NAME, key)
                except keyring.errors.PasswordDeleteError:
                    pass  # Token doesn't exist, ignore

            logger.info("Tokens cleared from Windows Credential Manager")

        except Exception as e:
            logger.error(f"Failed to clear tokens: {e}")

    def is_token_expired(self, expiry_str: Optional[str]) -> bool:
        """
        Check if token is expired.

        Args:
            expiry_str: ISO format expiry timestamp

        Returns:
            True if token is expired or invalid
        """
        if not expiry_str:
            return True

        try:
            expiry = datetime.fromisoformat(expiry_str)
            # Consider expired if less than 5 minutes remaining
            return datetime.now() >= (expiry - timedelta(minutes=5))
        except Exception:
            return True

    def refresh_access_token(self, refresh_token: str) -> Tuple[str, str, int]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: OAuth refresh token

        Returns:
            Tuple of (access_token, refresh_token, expires_in)

        Raises:
            TokenError: If token refresh fails
        """
        logger.info("Refreshing access token")

        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = b64encode(credentials.encode()).decode()

        try:
            response = requests.post(
                self.token_url,
                headers={
                    "Authorization": f"Basic {encoded_credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                timeout=30,
            )

            response.raise_for_status()
            data = response.json()

            access_token = data["access_token"]
            new_refresh_token = data.get("refresh_token", refresh_token)
            expires_in = data.get("expires_in", 3600)

            logger.info("Access token refreshed successfully")
            return access_token, new_refresh_token, expires_in

        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            raise TokenError(f"Failed to refresh token: {e}")

    def get_valid_access_token(self) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary.

        Returns:
            Valid access token or None if not authenticated

        Raises:
            TokenError: If token refresh fails
        """
        access_token, refresh_token, expiry_str = self.get_stored_tokens()

        if not access_token:
            logger.info("No stored access token found")
            return None

        # Check if token is expired
        if self.is_token_expired(expiry_str):
            if not refresh_token:
                logger.warning("Token expired and no refresh token available")
                return None

            # Refresh the token
            try:
                access_token, refresh_token, expires_in = self.refresh_access_token(
                    refresh_token
                )
                self.store_tokens(access_token, refresh_token, expires_in)
            except TokenError:
                logger.error("Failed to refresh token, user needs to re-authenticate")
                self.clear_tokens()
                return None

        return access_token

    def authorize(self, state: Optional[str] = None) -> str:
        """
        Start OAuth authorization flow.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL to open in browser
        """
        if state is None:
            state = secrets.token_urlsafe(32)

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.callback_url,
            "scope": "basic",
            "state": state,
        }

        auth_url = f"{self.authorize_url}?{urlencode(params)}"
        logger.info("Generated authorization URL")
        return auth_url

    def exchange_code_for_token(self, code: str) -> Tuple[str, str, int]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from callback

        Returns:
            Tuple of (access_token, refresh_token, expires_in)

        Raises:
            AuthenticationError: If token exchange fails
        """
        logger.info("Exchanging authorization code for token")

        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = b64encode(credentials.encode()).decode()

        try:
            response = requests.post(
                self.token_url,
                headers={
                    "Authorization": f"Basic {encoded_credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.callback_url,
                },
                timeout=30,
            )

            response.raise_for_status()
            data = response.json()

            access_token = data["access_token"]
            refresh_token = data.get("refresh_token", "")
            expires_in = data.get("expires_in", 3600)

            logger.info("Successfully exchanged code for token")
            return access_token, refresh_token, expires_in

        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
            raise AuthenticationError(f"Failed to exchange authorization code: {e}")


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP server handler for OAuth callback."""

    auth_code = None
    auth_state = None
    error = None

    def do_GET(self):
        """Handle GET request (OAuth callback)."""
        # Parse query parameters
        query_components = parse_qs(urlparse(self.path).query)

        # Extract code and state
        OAuthCallbackHandler.auth_code = query_components.get("code", [None])[0]
        OAuthCallbackHandler.auth_state = query_components.get("state", [None])[0]
        OAuthCallbackHandler.error = query_components.get("error", [None])[0]

        # Send response
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        if OAuthCallbackHandler.auth_code:
            html = """
            <html>
            <head><title>Authorization Successful</title></head>
            <body>
                <h1>✅ Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
            </body>
            </html>
            """
        else:
            html = f"""
            <html>
            <head><title>Authorization Failed</title></head>
            <body>
                <h1>❌ Authorization Failed</h1>
                <p>Error: {OAuthCallbackHandler.error or 'Unknown error'}</p>
                <p>Please close this window and try again.</p>
            </body>
            </html>
            """

        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        """Suppress log messages."""
        pass


def run_oauth_flow() -> bool:
    """
    Run interactive OAuth authorization flow.

    Returns:
        True if authorization successful, False otherwise
    """
    oauth = OAuthManager()

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Get authorization URL
    auth_url = oauth.authorize(state)

    print("\n" + "=" * 60)
    print("FatSecret OAuth Authorization")
    print("=" * 60)
    print("\n1. Opening your browser to authorize the application...")
    print("2. Please log in to FatSecret and grant permissions")
    print("3. You will be redirected back to this application\n")

    # Open browser
    webbrowser.open(auth_url)

    # Start local server for callback
    print("Waiting for authorization callback...")
    server_address = ("", 8080)
    httpd = HTTPServer(server_address, OAuthCallbackHandler)

    # Wait for callback (with timeout)
    httpd.timeout = 300  # 5 minutes
    httpd.handle_request()

    # Check if we got a code
    if not OAuthCallbackHandler.auth_code:
        print(f"\n❌ Authorization failed: {OAuthCallbackHandler.error or 'No code received'}")
        return False

    # Verify state (CSRF protection)
    if OAuthCallbackHandler.auth_state != state:
        print("\n❌ Authorization failed: Invalid state parameter")
        return False

    print("\n✅ Authorization code received!")
    print("Exchanging code for access token...")

    # Exchange code for token
    try:
        access_token, refresh_token, expires_in = oauth.exchange_code_for_token(
            OAuthCallbackHandler.auth_code
        )

        # Store tokens
        oauth.store_tokens(access_token, refresh_token, expires_in)

        print("\n✅ Success! Tokens stored in Windows Credential Manager")
        print("\nYou can now use the authenticated server with: python main.py")
        return True

    except AuthenticationError as e:
        print(f"\n❌ Failed to exchange code for token: {e}")
        return False
