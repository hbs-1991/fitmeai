"""Date utilities for FatSecret API.

FatSecret API uses "days since epoch" (Jan 1, 1970) for all date fields,
both in requests and responses.
"""

from datetime import date, timedelta

_EPOCH = date(1970, 1, 1)


def date_to_epoch_days(date_str: str) -> int:
    """Convert YYYY-MM-DD string to days since epoch (1970-01-01)."""
    return (date.fromisoformat(date_str) - _EPOCH).days


def epoch_days_to_date(days: int) -> str:
    """Convert days since epoch (1970-01-01) to YYYY-MM-DD string."""
    return (_EPOCH + timedelta(days=days)).isoformat()
