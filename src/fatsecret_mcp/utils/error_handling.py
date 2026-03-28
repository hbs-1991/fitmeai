"""Error handling utilities for FatSecret MCP Server."""


class FatSecretError(Exception):
    """Base exception for FatSecret MCP Server errors."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class AuthenticationError(FatSecretError):
    """Raised when authentication fails."""

    pass


class APIError(FatSecretError):
    """Raised when FatSecret API request fails."""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message, {"status_code": status_code, "response": response_data})
        self.status_code = status_code
        self.response_data = response_data


class ConfigurationError(FatSecretError):
    """Raised when configuration is invalid."""

    pass


class TokenError(AuthenticationError):
    """Raised when token operations fail."""

    pass
