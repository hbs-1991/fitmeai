"""MCP tools for weight management."""

from typing import Optional
from datetime import date
from ..api.base_client import FatSecretClient
from ..api.weight import WeightAPI
from ..utils import get_logger, APIError

logger = get_logger(__name__)


def register_weight_tools(mcp, client: FatSecretClient):
    """
    Register weight management tools with FastMCP server.

    Args:
        mcp: FastMCP server instance
        client: Authenticated FatSecretClient with user access token
    """
    weight_api = WeightAPI(client)

    @mcp.tool()
    def fatsecret_weight_update(
        weight_kg: float, entry_date: Optional[str] = None, comment: Optional[str] = None
    ) -> dict:
        """
        Update your weight for a specific date.

        This tool records your weight measurement for tracking over time.

        Args:
            weight_kg: Weight in kilograms (must be positive)
            entry_date: Date in YYYY-MM-DD format (default: today)
            comment: Optional note/comment (e.g., "Morning weight", "After workout")

        Returns:
            Dictionary containing:
            - success: True if update was successful
            - message: Success message
            - weight_kg: Weight that was recorded
            - date: Date of entry

        Example:
            Record today's weight:
            >>> result = fatsecret_weight_update(
            ...     weight_kg=70.5,
            ...     comment="Morning weight"
            ... )

            Record weight for specific date:
            >>> result = fatsecret_weight_update(
            ...     weight_kg=71.2,
            ...     entry_date="2026-02-01",
            ...     comment="After vacation"
            ... )
        """
        try:
            logger.info(f"Updating weight: {weight_kg} kg")

            if weight_kg <= 0:
                return {"error": "Weight must be positive"}

            if weight_kg > 500:
                return {"error": "Weight seems unrealistic (> 500 kg)"}

            if entry_date is None:
                entry_date = date.today().strftime("%Y-%m-%d")

            weight_api.update(weight_kg, entry_date, comment)

            return {
                "success": True,
                "message": "Weight updated successfully",
                "weight_kg": weight_kg,
                "date": entry_date,
            }

        except APIError as e:
            logger.error(f"API error in weight update: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in weight update: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

    @mcp.tool()
    def fatsecret_weight_get_month(
        year: Optional[int] = None, month: Optional[int] = None
    ) -> dict:
        """
        Get monthly weight history.

        This tool retrieves all weight measurements for a given month,
        useful for tracking weight trends over time.

        Args:
            year: Year (default: current year)
            month: Month 1-12 (default: current month)

        Returns:
            Dictionary containing:
            - year: Year of data
            - month: Month of data
            - weights: List of weight entries with:
              - date: Date in YYYY-MM-DD format
              - weight_kg: Weight in kilograms
              - weight_comment: Optional comment

        Example:
            Get current month:
            >>> result = fatsecret_weight_get_month()
            >>> for entry in result['weights']:
            ...     print(f"{entry['date']}: {entry['weight_kg']} kg")

            Get specific month:
            >>> result = fatsecret_weight_get_month(year=2026, month=1)

            Calculate weight change:
            >>> weights = result['weights']
            >>> if len(weights) >= 2:
            ...     change = weights[-1]['weight_kg'] - weights[0]['weight_kg']
            ...     print(f"Weight change: {change:+.1f} kg")
        """
        try:
            if year is None or month is None:
                today = date.today()
                year = year or today.year
                month = month or today.month

            logger.info(f"Getting weight month: {year}-{month:02d}")

            weights = weight_api.get_month(year, month)

            return {"year": year, "month": month, "weights": weights}

        except APIError as e:
            logger.error(f"API error in weight get month: {e}")
            return {"error": str(e), "weights": []}
        except Exception as e:
            logger.error(f"Unexpected error in weight get month: {e}")
            return {"error": f"Unexpected error: {str(e)}", "weights": []}

    logger.info("Registered weight management tools")
