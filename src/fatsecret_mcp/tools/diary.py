"""fatsecret_diary — read, write and summarize the food diary."""

from __future__ import annotations

from datetime import date

from ..api.food_diary import FoodDiaryAPI
from ..report import build as build_report
from ..utils import get_logger
from .dispatch import ActionError, guard, require, unknown

logger = get_logger(__name__)

ACTIONS = ("get", "month", "add", "edit", "delete", "report")
MEALS = ("breakfast", "lunch", "dinner", "other")


def _meal(value: str) -> str:
    if value.lower() not in MEALS:
        raise ActionError(f"meal {value!r} is not valid; use one of: {', '.join(MEALS)}")
    return value.lower()


def register_diary_tool(mcp, client) -> None:
    diary = FoodDiaryAPI(client)

    @mcp.tool()
    @guard
    def fatsecret_diary(
        action: str,
        entry_date: str | None = None,
        year: int | None = None,
        month: int | None = None,
        food_id: str | None = None,
        food_entry_name: str | None = None,
        serving_id: str | None = None,
        meal: str | None = None,
        number_of_units: float | None = None,
        food_entry_id: str | None = None,
        start: str | None = None,
        end: str | None = None,
        target_calories: float | None = None,
    ) -> dict:
        """Read, write and summarize the user's food diary.

        Actions:
          get     — entries and totals for one day. Optional: entry_date (today).
          month   — per-day totals for a month. Optional: year, month (current).
          add     — log a food. Requires: food_id, food_entry_name, serving_id, meal.
                    Optional: number_of_units (default 1.0), entry_date.
          edit    — change an entry. Requires: food_entry_id. Optional: serving_id,
                    number_of_units, meal.
          delete  — remove an entry. Requires: food_entry_id.
          report  — computed totals, averages, macro ratios and per-day rows for a
                    range. Requires: start, end (YYYY-MM-DD, ≤92 days). Optional:
                    target_calories, which adds days deviating over 20%.

        meal is one of: breakfast, lunch, dinner, other. Serving semantics — when
        number_of_units means grams — are in the nutrition-log skill; read it before
        logging. Returns {"error": "..."} rather than raising.
        """
        params = locals()
        if action == "get":
            when = entry_date or date.today().strftime("%Y-%m-%d")
            day = diary.get_entries(when)
            return {
                "date": day.date,
                "entries": [
                    {"food_entry_id": x.food_entry_id, "food_id": x.food_id,
                     "food_name": x.food_entry_name, "meal": x.meal,
                     "serving_id": x.serving_id, "number_of_units": x.number_of_units,
                     "calories": x.calories, "protein": x.protein, "fat": x.fat,
                     "carbohydrate": x.carbohydrate}
                    for x in day.entries
                ],
                "total_calories": day.total_calories,
                "total_protein": day.total_protein,
                "total_fat": day.total_fat,
                "total_carbohydrate": day.total_carbohydrate,
            }
        if action == "month":
            today = date.today()
            data = diary.get_month(year or today.year, month or today.month)
            return {"year": data.year, "month": data.month,
                    "days": [{"date": d.date, "calories": d.total_calories,
                              "protein": d.total_protein, "fat": d.total_fat,
                              "carbohydrate": d.total_carbohydrate}
                             for d in data.days]}
        if action == "add":
            fid, name, sid, ml = require(params, action, "food_id", "food_entry_name",
                                         "serving_id", "meal")
            entry_id = diary.add_entry(
                food_id=fid, serving_id=sid, meal=_meal(ml),
                number_of_units=1.0 if number_of_units is None else number_of_units,
                entry_date=entry_date, entry_name=name)
            return {"food_entry_id": entry_id, "message": f"added to {_meal(ml)}"}
        if action == "edit":
            (eid,) = require(params, action, "food_entry_id")
            diary.edit_entry(food_entry_id=eid, serving_id=serving_id,
                             number_of_units=number_of_units,
                             meal=_meal(meal) if meal else None)
            return {"success": True, "message": "diary entry updated"}
        if action == "delete":
            (eid,) = require(params, action, "food_entry_id")
            diary.delete_entry(eid)
            return {"success": True, "message": "diary entry deleted"}
        if action == "report":
            s, e = require(params, action, "start", "end")
            return build_report(diary, s, e, target_calories)
        return unknown(action, ACTIONS)

    logger.info("registered fatsecret_diary")
