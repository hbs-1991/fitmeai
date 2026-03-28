"""Base HTTP client with OAuth authentication for FatSecret API."""

import time
import requests
from base64 import b64encode
from typing import Optional, Dict, Any

from requests_oauthlib import OAuth1Session

from ..config import config
from ..utils import get_logger, APIError, AuthenticationError

logger = get_logger(__name__)


class FatSecretClient:
    """Base client for FatSecret Platform API.

    Public endpoints use OAuth 2.0 Client Credentials (Bearer token).
    User-specific endpoints use OAuth 1.0 signed requests.
    """

    def __init__(self, access_token: Optional[str] = None) -> None:
        """
        Initialize FatSecret API client.

        Args:
            access_token: OAuth 1.0 access token for authenticated requests.
                         If None, only public API (Client Credentials) is available.
        """
        self.base_url = config.API_BASE_URL
        self._oauth1_token = access_token
        self._oauth1_secret: Optional[str] = None
        self._cc_token: Optional[str] = None
        self._cc_expiry: float = 0

        # If access_token provided, load the matching secret from keyring
        if access_token:
            self._load_oauth1_secret()

    def _load_oauth1_secret(self) -> None:
        """Load OAuth 1.0 token secret from keyring to pair with the token."""
        from ..auth.oauth_manager import OAuthManager

        mgr = OAuthManager()
        _, secret = mgr.get_stored_tokens()
        self._oauth1_secret = secret

    # ── OAuth 2.0 Client Credentials (public API) ──────────────────

    def _get_client_credentials_token(self) -> str:
        """Get/refresh a Bearer token via Client Credentials flow."""
        if self._cc_token and time.time() < self._cc_expiry:
            return self._cc_token

        logger.info("Obtaining client credentials token")
        credentials = f"{config.CLIENT_ID}:{config.CLIENT_SECRET}"
        encoded = b64encode(credentials.encode()).decode()

        try:
            resp = requests.post(
                config.OAUTH2_TOKEN_URL,
                headers={
                    "Authorization": f"Basic {encoded}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "client_credentials",
                    "scope": "basic barcode premier",
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            self._cc_token = data["access_token"]
            self._cc_expiry = time.time() + data.get("expires_in", 3600) - 60
            logger.info("Client credentials token obtained")
            return self._cc_token

        except requests.RequestException as e:
            raise AuthenticationError(f"Client Credentials auth failed: {e}")

    # ── Requests ───────────────────────────────────────────────────

    def request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        require_auth: bool = False,
    ) -> Dict[str, Any]:
        """Make a request to FatSecret API.

        Args:
            method: API method name (e.g. 'foods.search')
            params: Additional method parameters
            require_auth: True = user-level OAuth 1.0, False = public OAuth 2.0
        """
        request_params = dict(params or {})
        request_params["method"] = method
        request_params["format"] = "json"

        if require_auth:
            return self._request_oauth1(request_params)
        return self._request_oauth2(request_params)

    def _request_oauth2(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Public API call with Bearer token."""
        token = self._get_client_credentials_token()
        try:
            resp = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data=params,
                timeout=30,
            )
            return self._handle_response(resp)
        except requests.RequestException as e:
            raise APIError(f"Request failed: {e}")

    def _request_oauth1(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """User-level API call with OAuth 1.0 signature."""
        if not self._oauth1_token or not self._oauth1_secret:
            raise AuthenticationError(
                "User authentication required. Run: python setup_oauth.py"
            )

        oauth = OAuth1Session(
            client_key=config.CLIENT_ID,
            client_secret=config.CLIENT_SECRET,
            resource_owner_key=self._oauth1_token,
            resource_owner_secret=self._oauth1_secret,
        )
        try:
            resp = oauth.post(self.base_url, data=params, timeout=30)
            return self._handle_response(resp)
        except requests.RequestException as e:
            raise APIError(f"Request failed: {e}")

    def _handle_response(self, resp: requests.Response) -> Dict[str, Any]:
        """Parse response, raise on errors."""
        if resp.status_code != 200:
            error_data = None
            try:
                error_data = resp.json()
            except Exception:
                pass
            logger.error(f"API {resp.status_code}: {resp.text[:200]}")
            raise APIError(
                f"API request failed ({resp.status_code})",
                status_code=resp.status_code,
                response_data=error_data,
            )

        data = resp.json()
        if "error" in data:
            msg = data.get("error", {}).get("message", "Unknown error")
            raise APIError(f"API error: {msg}", response_data=data)
        return data

    # ── Convenience ────────────────────────────────────────────────

    def get(self, method: str, **params) -> Dict[str, Any]:
        return self.request(method, params, require_auth=False)

    def post(self, method: str, require_auth: bool = True, **params) -> Dict[str, Any]:
        return self.request(method, params, require_auth=require_auth)
