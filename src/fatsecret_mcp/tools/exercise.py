"""fatsecret_exercise — exercise lookup and the activity log."""

from __future__ import annotations

from datetime import date

from ..api.exercise import ExerciseAPI
from ..utils import get_logger
from .dispatch import guard, require, unknown

logger = get_logger(__name__)

ACTIONS = ("search", "get", "month", "add", "edit")


def register_exercise_tool(mcp, client) -> None:
    api = ExerciseAPI(client)

    @mcp.tool()
    @guard
    def fatsecret_exercise(
        action: str,
        query: str | None = None,
        entry_date: str | None = None,
        year: int | None = None,
        month: int | None = None,
        exercise_id: str | None = None,
        minutes: float | None = None,
        exercise_entry_id: str | None = None,
        max_results: int = 20,
    ) -> dict:
        """Look up exercises and manage the activity log.

        Actions:
          search — find exercises by name. Requires: query.
          get    — entries for one day. Optional: entry_date (today).
          month  — per-day totals for a month. Optional: year, month (current).
          add    — log activity. Requires: exercise_id, minutes. Optional: entry_date.
          edit   — change duration. Requires: exercise_entry_id, minutes.

        FatSecret's day is fully allocated: adding an exercise reduces the minutes
        credited to the default resting activity. Returns {"error": "..."} on failure.
        """
        params = locals()
        if action == "search":
            (q,) = require(params, action, "query")
            return {"exercises": api.search(q, max_results=max_results)}
        if action == "get":
            return {"entries": api.get_entries(
                entry_date or date.today().strftime("%Y-%m-%d"))}
        if action == "month":
            today = date.today()
            return {"month": api.get_month(year or today.year, month or today.month)}
        if action == "add":
            eid, mins = require(params, action, "exercise_id", "minutes")
            return {"exercise_entry_id": api.add_entry(
                exercise_id=eid, minutes=mins, entry_date=entry_date),
                "message": f"logged {mins} minutes"}
        if action == "edit":
            eid, mins = require(params, action, "exercise_entry_id", "minutes")
            api.edit_entry(exercise_entry_id=eid, minutes=mins)
            return {"success": True, "message": "exercise entry updated"}
        return unknown(action, ACTIONS)

    logger.info("registered fatsecret_exercise")
