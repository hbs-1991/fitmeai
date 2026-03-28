"""API response models."""

from typing import Any, Optional, Dict
from pydantic import BaseModel


class APIResponse(BaseModel):
    """Generic API response wrapper."""

    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    error_description: Optional[str] = None
    error_code: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
