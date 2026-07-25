"""fatsecret_weight — weight log."""

from __future__ import annotations

from datetime import date

from ..api.weight import WeightAPI
from ..utils import get_logger
from .dispatch import guard, require, unknown

logger = get_logger(__name__)

ACTIONS = ("update", "month")


def register_weight_tool(mcp, client) -> None:
    api = WeightAPI(client)

    @mcp.tool()
    @guard
    def fatsecret_weight(
        action: str,
        weight_kg: float | None = None,
        entry_date: str | None = None,
        comment: str | None = None,
        year: int | None = None,
        month: int | None = None,
    ) -> dict:
        """Record and read the user's weight history.

        Actions:
          update — set the weight for a date. Requires: weight_kg (kilograms).
                   Optional: entry_date (today), comment.
          month  — weight entries for a month. Optional: year, month (current).

        Returns {"error": "..."} on failure rather than raising.
        """
        params = locals()
        if action == "update":
            (kg,) = require(params, action, "weight_kg")
            api.update(kg, entry_date, comment)
            return {"success": True, "message": f"weight set to {kg} kg"}
        if action == "month":
            today = date.today()
            return {"month": api.get_month(year or today.year, month or today.month)}
        return unknown(action, ACTIONS)

    logger.info("registered fatsecret_weight")
