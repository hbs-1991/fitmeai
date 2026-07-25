"""report.build: the deterministic half. This is arithmetic the model must never do
token-by-token — a week of raw entries is ~30 verbose JSON rows to sum by hand."""
import pytest

from fatsecret_mcp.report import build


class Day:
    def __init__(self, d, cal, carb, prot, fat):
        self.date, self.total_calories = d, cal
        self.total_carbohydrate, self.total_protein, self.total_fat = carb, prot, fat


class Month:
    def __init__(self, year, month, days):
        self.year, self.month, self.days = year, month, days


class FakeDiary:
    def __init__(self, months):
        self._months, self.fetched = months, []

    def get_month(self, year, month):
        self.fetched.append((year, month))
        return self._months.get((year, month), Month(year, month, []))


WEEK = FakeDiary({(2026, 7): Month(2026, 7, [
    Day("2026-07-20", 2000, 200, 150, 60),
    Day("2026-07-21", 2200, 220, 150, 70),
    Day("2026-07-22", 1500, 150, 120, 45),
    Day("2026-07-99", 9999, 0, 0, 0),      # nonsense date: must be filtered out
])})


def test_only_days_inside_the_range_are_counted():
    out = build(WEEK, "2026-07-20", "2026-07-21", None)
    assert out["days_logged"] == 2
    assert out["totals"]["calories"] == 4200
    assert [r["date"] for r in out["rows"]] == ["2026-07-20", "2026-07-21"]


def test_averages_divide_by_days_logged_not_days_in_range():
    """Six days in the range, three logged. Dividing by 6 invents a deficit that
    is really just days the user forgot to log."""
    out = build(WEEK, "2026-07-20", "2026-07-25", None)
    assert out["days_logged"] == 3
    assert out["averages"]["calories"] == pytest.approx(1900.0)


def test_macro_ratios_are_percentages_of_calories_and_sum_to_100():
    out = build(WEEK, "2026-07-20", "2026-07-22", None)
    r = out["macro_ratio_pct"]
    assert sum(r.values()) == pytest.approx(100.0, abs=0.6)
    assert r["protein"] > r["fat"]


def test_a_target_flags_days_deviating_by_more_than_20_percent():
    out = build(WEEK, "2026-07-20", "2026-07-22", 2000.0)
    assert out["off_target_days"] == [{"date": "2026-07-22", "calories": 1500,
                                       "deviation_pct": -25.0}]


def test_no_target_means_no_deviation_keys():
    out = build(WEEK, "2026-07-20", "2026-07-22", None)
    assert "off_target_days" not in out


def test_a_range_spanning_two_months_fetches_each_month_once():
    """One API call per month, not per day — a 30-day report must not be 30 calls."""
    d = FakeDiary({})
    build(d, "2026-06-28", "2026-07-03", None)
    assert d.fetched == [(2026, 6), (2026, 7)]


def test_an_inverted_range_is_rejected():
    with pytest.raises(Exception, match="before"):
        build(WEEK, "2026-07-22", "2026-07-20", None)


def test_an_absurd_range_is_rejected():
    with pytest.raises(Exception, match="92"):
        build(WEEK, "2026-01-01", "2026-12-31", None)


def test_an_empty_range_reports_zero_days_without_dividing_by_zero():
    out = build(FakeDiary({}), "2026-07-20", "2026-07-22", 2000.0)
    assert out["days_logged"] == 0
    assert out["averages"]["calories"] == 0
