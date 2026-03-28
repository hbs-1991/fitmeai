"""Base HTTP client with OAuth authentication for FatSecret API."""

import time
import requests
from typing import Optional, Dict, Any
from base64 import b64encode

from ..config import config
from ..utils import get_logger, APIError, AuthenticationError

logger = get_logger(__name__)


class FatSecretClient:
    """Base client for FatSecret Platform API with OAuth 2.0 authentication."""

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize FatSecret API client.

        Args:
            access_token: OAuth access token for authenticated requests.
                         If None, will use Client Credentials flow for public API.
        """
        self.base_url = config.API_BASE_URL
        self.access_token = access_token
        self._client_credentials_token = None
        self._token_expiry = 0

    def _get_client_credentials_token(self) -> str:
        """
        Get OAuth token using Client Credentials flow.

        Returns:
            Access token for public API access.

        Raises:
            AuthenticationError: If authentication fails.
        """
        # Check if cached token is still valid
        if self._client_credentials_token and time.time() < self._token_expiry:
            return self._client_credentials_token

        logger.info("Obtaining new client credentials token")

        # Prepare credentials
        credentials = f"{config.CLIENT_ID}:{config.CLIENT_SECRET}"
        encoded_credentials = b64encode(credentials.encode()).decode()

        # Request token
        try:
            response = requests.post(
                config.OAUTH_TOKEN_URL,
                headers={
                    "Authorization": f"Basic {encoded_credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "client_credentials",
                    "scope": "basic",
                },
                timeout=30,
            )
            response.raise_for_status()
            token_data = response.json()

            self._client_credentials_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self._token_expiry = time.time() + expires_in - 60  # Refresh 1 min early

            logger.info("Successfully obtained client credentials token")
            return self._client_credentials_token

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to obtain client credentials token: {e}")
            raise AuthenticationError(f"Failed to authenticate with FatSecret API: {e}")

    def request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        require_auth: bool = False,
    ) -> Dict[str, Any]:
        """
        Make authenticated request to FatSecret API.

        Args:
            method: FatSecret API method name (e.g., 'foods.search')
            params: Additional parameters for the API method
            require_auth: If True, requires user access token

        Returns:
            API response data as dictionary

        Raises:
            AuthenticationError: If authentication fails
            APIError: If API request fails
        """
        # Determine which token to use
        if require_auth:
            if not self.access_token:
                raise AuthenticationError(
                    "This operation requires user authentication. "
                    "Please run setup_oauth.py first."
                )
            token = self.access_token
        else:
            # Use client credentials for public API
            token = self._get_client_credentials_token()

        # Prepare request
        request_params = params or {}
        request_params["method"] = method
        request_params["format"] = "json"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        logger.debug(f"API Request: {method} with params: {request_params}")

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=request_params,
                timeout=30,
            )

            # Check for HTTP errors
            if response.status_code != 200:
                error_data = None
                try:
                    error_data = response.json()
                except Exception:
                    pass

                logger.error(
                    f"API request failed: {response.status_code} - {response.text}"
                )
                raise APIError(
                    f"API request failed with status {response.status_code}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            # Parse response
            data = response.json()

            # Check for API-level errors
            if "error" in data:
                error_msg = data.get("error", {}).get("message", "Unknown error")
                logger.error(f"API error: {error_msg}")
                raise APIError(f"API error: {error_msg}", response_data=data)

            logger.debug(f"API Response: {data}")
            return data

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for method: {method}")
            raise APIError("Request timed out")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for method {method}: {e}")
            raise APIError(f"Request failed: {e}")

    def get(self, method: str, **params) -> Dict[str, Any]:
        """
        Convenience method for GET-like requests.

        Args:
            method: API method name
            **params: Method parameters

        Returns:
            API response data
        """
        return self.request(method, params, require_auth=False)

    def post(self, method: str, require_auth: bool = True, **params) -> Dict[str, Any]:
        """
        Convenience method for POST-like requests (usually require auth).

        Args:
            method: API method name
            require_auth: Whether user authentication is required
            **params: Method parameters

        Returns:
            API response data
        """
        return self.request(method, params, require_auth=require_auth)
