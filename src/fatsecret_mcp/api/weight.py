"""Weight management API client for FatSecret Platform API."""

from typing import Optional, List, Dict, Any
from datetime import date
from ..utils import get_logger
from .base_client import FatSecretClient

logger = get_logger(__name__)


class WeightAPI:
    """Client for FatSecret Weight Management API."""

    def __init__(self, client: FatSecretClient):
        """
        Initialize Weight API client.

        Args:
            client: Authenticated FatSecret client with user access token
        """
        self.client = client

    def update(
        self,
        weight_kg: float,
        entry_date: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> bool:
        """
        Update weight for a specific date.

        Args:
            weight_kg: Weight in kilograms
            entry_date: Date in YYYY-MM-DD format (default: today)
            comment: Optional comment/note

        Returns:
            True if successful

        Example:
            >>> api = WeightAPI(client)
            >>> api.update(weight_kg=70.5, comment="Morning weight")
        """
        if entry_date is None:
            entry_date = date.today().strftime("%Y-%m-%d")

        logger.info(f"Updating weight for {entry_date}: {weight_kg} kg")

        params = {
            "weight_kg": weight_kg,
            "date": entry_date,
        }

        if comment:
            params["comment"] = comment

        self.client.post("weight.update", require_auth=True, **params)

        logger.info(f"Updated weight successfully")
        return True

    def get_month(
        self, year: Optional[int] = None, month: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get monthly weight history.

        Args:
            year: Year (default: current year)
            month: Month 1-12 (default: current month)

        Returns:
            List of weight entries with date, weight, and comment

        Example:
            >>> api = WeightAPI(client)
            >>> weights = api.get_month(2026, 2)
            >>> for entry in weights:
            ...     print(f"{entry['date']}: {entry['weight_kg']} kg")
        """
        if year is None or month is None:
            today = date.today()
            year = year or today.year
            month = month or today.month

        logger.info(f"Getting weight month: {year}-{month:02d}")

        response = self.client.post(
            "weights.get_month", require_auth=True, year=year, month=month
        )

        # Parse response
        weights = []
        month_data = response.get("month", {})
        day_list = month_data.get("day", [])

        # Ensure it's a list
        if isinstance(day_list, dict):
            day_list = [day_list]

        for day_data in day_list:
            day_date = day_data.get("date_int")  # Format: YYYYMMDD
            if day_date:
                # Convert YYYYMMDD to YYYY-MM-DD
                date_str = f"{day_date[:4]}-{day_date[4:6]}-{day_date[6:8]}"

                weight_entry = {
                    "date": date_str,
                    "weight_kg": self._parse_float(day_data.get("weight_kg")),
                    "weight_comment": day_data.get("weight_comment"),
                }
                weights.append(weight_entry)

        logger.info(f"Retrieved {len(weights)} weight entries for {year}-{month:02d}")
        return weights

    @staticmethod
    def _parse_float(value) -> Optional[float]:
        """Parse value to float, return None if invalid."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
