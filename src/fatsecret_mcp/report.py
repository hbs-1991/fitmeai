"""Period aggregation over the food diary.

Server-side because it needs credentials, and compressed because raw diary JSON is
the single most expensive thing this integration could put in a model's context.
"""

from __future__ import annotations

from datetime import date

from .utils import ActionError

MAX_RANGE_DAYS = 92
DEVIATION_THRESHOLD_PCT = 20.0
_KCAL_PER_G = {"protein": 4.0, "fat": 9.0, "carbohydrate": 4.0}


def _months_between(start: date, end: date) -> list[tuple[int, int]]:
    out, y, m = [], start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def build(diary_api, start: str, end: str, target_calories: float | None) -> dict:
    """Daily rows plus period totals, averages and macro ratios for [start, end].

    Fetches one month at a time (get_month returns per-day totals in a single call),
    never one call per day.
    """
    try:
        s, e = date.fromisoformat(start), date.fromisoformat(end)
    except ValueError as exc:
        raise ActionError(f"start and end must be YYYY-MM-DD: {exc}") from exc
    if e < s:
        raise ActionError(f"end {end} is before start {start}")
    if (e - s).days + 1 > MAX_RANGE_DAYS:
        raise ActionError(f"range is longer than {MAX_RANGE_DAYS} days; "
                          f"ask for a shorter period")

    rows: list[dict] = []
    for year, month in _months_between(s, e):
        for day in getattr(diary_api.get_month(year, month), "days", []):
            try:
                d = date.fromisoformat(day.date)
            except (ValueError, TypeError):
                continue          # the API has returned malformed dates; skip, don't crash
            if s <= d <= e:
                rows.append({
                    "date": day.date,
                    "calories": day.total_calories,
                    "protein": day.total_protein,
                    "fat": day.total_fat,
                    "carbohydrate": day.total_carbohydrate,
                })
    rows.sort(key=lambda r: r["date"])

    keys = ("calories", "protein", "fat", "carbohydrate")
    totals = {k: round(sum(r[k] or 0 for r in rows), 1) for k in keys}
    n = len(rows)
    # Averages divide by days LOGGED, not days in the range: an unlogged day is
    # missing data, not a zero-calorie day, and averaging it in invents a deficit.
    averages = {k: round(totals[k] / n, 1) if n else 0 for k in keys}

    macro_kcal = {m: totals[m] * f for m, f in _KCAL_PER_G.items()}
    total_macro_kcal = sum(macro_kcal.values())
    ratios = ({m: round(v / total_macro_kcal * 100, 1) for m, v in macro_kcal.items()}
              if total_macro_kcal else {m: 0.0 for m in _KCAL_PER_G})

    out = {
        "start": start, "end": end, "days_in_range": (e - s).days + 1,
        "days_logged": n, "rows": rows, "totals": totals, "averages": averages,
        "macro_ratio_pct": ratios,
    }
    if target_calories:
        out["target_calories"] = target_calories
        out["off_target_days"] = [
            {"date": r["date"], "calories": r["calories"],
             "deviation_pct": round(((r["calories"] or 0) - target_calories)
                                    / target_calories * 100, 1)}
            for r in rows
            if abs((r["calories"] or 0) - target_calories) / target_calories * 100
            > DEVIATION_THRESHOLD_PCT
        ]
    return out
