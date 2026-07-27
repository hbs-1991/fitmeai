"""How a month is selected on the *_entries.get_month endpoints.

FatSecret does not take `year`/`month` on these methods — it takes `date`, any day
inside the wanted month, as days-since-epoch. Passing year/month is not an error:
the API ignores the unknown parameters and silently returns the CURRENT month.

Verified against the live API:

    year=2026, month=6            -> window 2026-07-01 .. 2026-07-31   (wrong)
    date=<epoch days 2026-06-15>  -> window 2026-06-01 .. 2026-06-30   (right)

That silence is what makes it dangerous. report.build() calls get_month() once per
month in the range, so before this fix a June–July report read July twice and never
saw June — while looking perfectly healthy, because every call returned real data.
The tool tests never caught it: they drive fakes, and a fake honours whatever
keyword it is handed.
"""

from fatsecret_mcp.api.food_diary import FoodDiaryAPI
from fatsecret_mcp.api.weight import WeightAPI
from fatsecret_mcp.api.date_utils import epoch_days_to_date

MONTH_RESPONSE = {"month": {"day": [], "from_date_int": "20635",
                            "to_date_int": "20665"}}


class RecordingClient:
    """Captures the parameters actually put on the wire."""

    def __init__(self):
        self.calls = []

    def post(self, method, require_auth=True, **params):
        self.calls.append((method, params))
        return MONTH_RESPONSE

    def get(self, method, **params):
        self.calls.append((method, params))
        return MONTH_RESPONSE


def _only_call(api_call, expected_method):
    client = RecordingClient()
    api_call(client)
    assert len(client.calls) == 1, client.calls
    method, params = client.calls[0]
    assert method == expected_method
    return params


def test_food_diary_get_month_selects_the_month_with_a_date():
    params = _only_call(lambda c: FoodDiaryAPI(c).get_month(2026, 6),
                        "food_entries.get_month")
    assert "year" not in params and "month" not in params, (
        "FatSecret ignores year/month here and returns the current month instead")
    assert epoch_days_to_date(params["date"]).startswith("2026-06")


def test_weight_get_month_selects_the_month_with_a_date():
    params = _only_call(lambda c: WeightAPI(c).get_month(2026, 6),
                        "weights.get_month")
    assert "year" not in params and "month" not in params
    assert epoch_days_to_date(params["date"]).startswith("2026-06")


def test_the_chosen_day_is_mid_month():
    """Day 1 or 31 sits on a boundary that a timezone shift can push into the
    neighbouring month. Mid-month cannot be moved out of its own month."""
    for api_call, method in ((lambda c: FoodDiaryAPI(c).get_month(2026, 2),
                              "food_entries.get_month"),
                             (lambda c: WeightAPI(c).get_month(2026, 2),
                              "weights.get_month")):
        params = _only_call(api_call, method)
        day = int(epoch_days_to_date(params["date"]).split("-")[2])
        assert 10 <= day <= 20, f"{method} picked day {day}"


def test_december_does_not_roll_into_the_next_year():
    params = _only_call(lambda c: FoodDiaryAPI(c).get_month(2025, 12),
                        "food_entries.get_month")
    assert epoch_days_to_date(params["date"]).startswith("2025-12")


def test_a_report_spanning_two_months_asks_for_two_different_months():
    """The regression that matters: report.build fetches one month at a time, so two
    months in the range must produce two DIFFERENT date parameters. Identical ones
    mean the second month silently re-read the first."""
    from fatsecret_mcp.report import build

    client = RecordingClient()
    build(FoodDiaryAPI(client), "2026-06-28", "2026-07-03", None)

    dates = [epoch_days_to_date(p["date"])[:7] for _, p in client.calls]
    assert dates == ["2026-06", "2026-07"], dates
