"""fatsecret_diary: six actions over the food diary."""
from tests.test_tool_food import FakeMCP


class FakeDiaryAPI:
    def __init__(self):
        self.calls = []

    def get_entries(self, entry_date):
        self.calls.append(("get_entries", entry_date))
        return type("D", (), {"date": entry_date, "entries": [], "total_calories": 0,
                              "total_carbohydrate": 0, "total_protein": 0,
                              "total_fat": 0})()

    def get_month(self, year, month):
        self.calls.append(("get_month", year, month))
        return type("M", (), {"year": year, "month": month, "days": []})()

    def add_entry(self, **kw):
        self.calls.append(("add_entry", kw))
        return "999"

    def edit_entry(self, **kw):
        self.calls.append(("edit_entry", kw))

    def delete_entry(self, food_entry_id):
        self.calls.append(("delete_entry", food_entry_id))


def build(monkeypatch):
    from fatsecret_mcp.tools import diary as diary_mod
    mcp, fake = FakeMCP(), FakeDiaryAPI()
    monkeypatch.setattr(diary_mod, "FoodDiaryAPI", lambda client: fake)
    diary_mod.register_diary_tool(mcp, client=object())
    return mcp.tools["fatsecret_diary"], fake


def test_get_defaults_to_today(monkeypatch):
    tool, fake = build(monkeypatch)
    tool(action="get")
    assert fake.calls[0][1] is not None


def test_add_requires_the_four_identifying_fields(monkeypatch):
    tool, _ = build(monkeypatch)
    out = tool(action="add", food_id="1641")
    for name in ("food_entry_name", "serving_id", "meal"):
        assert name in out["error"]


def test_add_rejects_an_invalid_meal_by_naming_the_valid_ones(monkeypatch):
    tool, _ = build(monkeypatch)
    out = tool(action="add", food_id="1", food_entry_name="x", serving_id="2",
               meal="brunch")
    assert "brunch" in out["error"] and "breakfast" in out["error"]


def test_add_lowercases_the_meal_and_defaults_units_to_one(monkeypatch):
    tool, fake = build(monkeypatch)
    tool(action="add", food_id="1", food_entry_name="x", serving_id="2", meal="Lunch")
    kw = fake.calls[0][1]
    assert kw["meal"] == "lunch" and kw["number_of_units"] == 1.0


def test_delete_requires_an_entry_id(monkeypatch):
    tool, _ = build(monkeypatch)
    assert "food_entry_id" in tool(action="delete")["error"]


def test_report_requires_both_range_ends(monkeypatch):
    tool, _ = build(monkeypatch)
    out = tool(action="report", start="2026-07-20")
    assert "end" in out["error"]


def test_report_returns_the_computed_shape(monkeypatch):
    tool, _ = build(monkeypatch)
    out = tool(action="report", start="2026-07-20", end="2026-07-22")
    assert set(out) >= {"days_logged", "totals", "averages", "macro_ratio_pct"}


def test_an_unknown_action_is_an_error(monkeypatch):
    tool, _ = build(monkeypatch)
    assert "error" in tool(action="summarise")
