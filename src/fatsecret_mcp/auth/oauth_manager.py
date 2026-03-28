"""OAuth 1.0 three-legged authentication manager for FatSecret API."""

import keyring
import secrets
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Tuple
from urllib.parse import parse_qs, urlparse

from requests_oauthlib import OAuth1Session

from ..config import config
from ..utils import get_logger, AuthenticationError, TokenError

logger = get_logger(__name__)


class OAuthManager:
    """Manages OAuth 1.0 three-legged flow and token storage via keyring."""

    SERVICE_NAME = "fatsecret_mcp"
    KEY_ACCESS_TOKEN = "oauth1_access_token"
    KEY_ACCESS_SECRET = "oauth1_access_secret"

    def __init__(self) -> None:
        self.consumer_key = config.CLIENT_ID
        self.consumer_secret = config.CLIENT_SECRET
        self.callback_url = config.OAUTH_CALLBACK_URL

    # ── Token Storage ──────────────────────────────────────────────

    def store_tokens(self, access_token: str, access_secret: str) -> None:
        """Store OAuth 1.0 access token + secret in keyring."""
        try:
            keyring.set_password(self.SERVICE_NAME, self.KEY_ACCESS_TOKEN, access_token)
            keyring.set_password(self.SERVICE_NAME, self.KEY_ACCESS_SECRET, access_secret)
            logger.info("OAuth 1.0 tokens stored in keyring")
        except Exception as e:
            raise TokenError(f"Failed to store tokens: {e}")

    def get_stored_tokens(self) -> Tuple[Optional[str], Optional[str]]:
        """Retrieve stored OAuth 1.0 access token + secret."""
        try:
            token = keyring.get_password(self.SERVICE_NAME, self.KEY_ACCESS_TOKEN)
            secret = keyring.get_password(self.SERVICE_NAME, self.KEY_ACCESS_SECRET)
            return token, secret
        except Exception as e:
            logger.error(f"Failed to retrieve tokens: {e}")
            return None, None

    def clear_tokens(self) -> None:
        """Remove stored tokens from keyring."""
        for key in (self.KEY_ACCESS_TOKEN, self.KEY_ACCESS_SECRET):
            try:
                keyring.delete_password(self.SERVICE_NAME, key)
            except keyring.errors.PasswordDeleteError:
                pass
        logger.info("OAuth 1.0 tokens cleared")

    # ── Public API ─────────────────────────────────────────────────

    def get_valid_access_token(self) -> Optional[str]:
        """Return access_token if stored, else None.

        OAuth 1.0 tokens don't expire on their own — they remain valid
        until the user revokes access.  We simply check presence.
        """
        token, secret = self.get_stored_tokens()
        if token and secret:
            return token
        return None

    def get_oauth1_session(self) -> Optional[OAuth1Session]:
        """Build a fully-signed OAuth1Session for authenticated API calls."""
        token, secret = self.get_stored_tokens()
        if not token or not secret:
            return None
        return OAuth1Session(
            client_key=self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=token,
            resource_owner_secret=secret,
        )

    # ── Three-Legged Flow ──────────────────────────────────────────

    def fetch_request_token(self) -> Tuple[str, str]:
        """Step 1: Get a request token from FatSecret."""
        oauth = OAuth1Session(
            client_key=self.consumer_key,
            client_secret=self.consumer_secret,
            callback_uri=self.callback_url,
        )
        try:
            resp = oauth.fetch_request_token(config.OAUTH1_REQUEST_TOKEN_URL)
        except Exception as e:
            raise AuthenticationError(f"Failed to get request token: {e}")

        return resp["oauth_token"], resp["oauth_token_secret"]

    def build_authorize_url(self, request_token: str) -> str:
        """Step 2: Build the URL to redirect the user to."""
        return f"{config.OAUTH1_AUTHORIZE_URL}?oauth_token={request_token}"

    def fetch_access_token(
        self,
        request_token: str,
        request_secret: str,
        verifier: str,
    ) -> Tuple[str, str]:
        """Step 3: Exchange request token + verifier for access token."""
        oauth = OAuth1Session(
            client_key=self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=request_token,
            resource_owner_secret=request_secret,
        )
        oauth._client.client.verifier = verifier
        try:
            resp = oauth.fetch_access_token(config.OAUTH1_ACCESS_TOKEN_URL)
        except Exception as e:
            raise AuthenticationError(f"Failed to get access token: {e}")

        return resp["oauth_token"], resp["oauth_token_secret"]


# ── Callback HTTP Handler ──────────────────────────────────────────


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Tiny HTTP handler that captures the oauth_token + oauth_verifier."""

    oauth_token: Optional[str] = None
    oauth_verifier: Optional[str] = None
    error: Optional[str] = None

    def do_GET(self) -> None:
        qs = parse_qs(urlparse(self.path).query)
        _OAuthCallbackHandler.oauth_token = qs.get("oauth_token", [None])[0]
        _OAuthCallbackHandler.oauth_verifier = qs.get("oauth_verifier", [None])[0]

        ok = bool(_OAuthCallbackHandler.oauth_verifier)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        if ok:
            html = (
                "<html><body>"
                "<h1>Авторизация прошла успешно!</h1>"
                "<p>Можно закрыть это окно и вернуться в терминал.</p>"
                "</body></html>"
            )
        else:
            _OAuthCallbackHandler.error = qs.get("error", ["unknown"])[0]
            html = (
                "<html><body>"
                f"<h1>Ошибка авторизации</h1><p>{_OAuthCallbackHandler.error}</p>"
                "</body></html>"
            )
        self.wfile.write(html.encode())

    def log_message(self, format, *args) -> None:  # noqa: A002
        pass  # suppress console noise


# ── Interactive Flow ───────────────────────────────────────────────


def run_oauth_flow() -> bool:
    """Run the full interactive 3-legged OAuth 1.0 flow.

    1. Fetch request token
    2. Open browser → user authorises → callback with verifier
    3. Exchange for access token
    4. Store in keyring

    Returns True on success.
    """
    oauth = OAuthManager()

    # Step 1 — request token
    print("\n1. Получаю request token...")
    try:
        req_token, req_secret = oauth.fetch_request_token()
    except AuthenticationError as e:
        print(f"\n❌ Не удалось получить request token: {e}")
        return False
    print("   ✅ Request token получен")

    # Step 2 — open browser
    auth_url = oauth.build_authorize_url(req_token)
    print("\n2. Открываю браузер для авторизации...")
    print(f"   URL: {auth_url}")
    webbrowser.open(auth_url)

    # Start local callback server
    print("\n   Жду callback от FatSecret...")
    _OAuthCallbackHandler.oauth_token = None
    _OAuthCallbackHandler.oauth_verifier = None
    _OAuthCallbackHandler.error = None

    httpd = HTTPServer(("", 8080), _OAuthCallbackHandler)
    httpd.timeout = 300  # 5 minutes
    httpd.handle_request()

    verifier = _OAuthCallbackHandler.oauth_verifier
    if not verifier:
        print(f"\n❌ Авторизация не удалась: {_OAuthCallbackHandler.error or 'нет verifier'}")
        return False
    print("   ✅ Verifier получен")

    # Step 3 — access token
    print("\n3. Обмениваю на access token...")
    try:
        access_token, access_secret = oauth.fetch_access_token(
            req_token, req_secret, verifier
        )
    except AuthenticationError as e:
        print(f"\n❌ Не удалось получить access token: {e}")
        return False

    # Store
    oauth.store_tokens(access_token, access_secret)
    print("   ✅ Токены сохранены в Windows Credential Manager")
    return True
