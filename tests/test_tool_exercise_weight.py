from tests.test_tool_food import FakeMCP


class FakeExercise:
    def __init__(self):
        self.calls = []

    def search(self, search_expression, max_results=50):
        self.calls.append(("search", search_expression)); return {"exercises": []}

    def get_entries(self, entry_date):
        self.calls.append(("get_entries", entry_date)); return {"entries": []}

    def get_month(self, year, month):
        self.calls.append(("get_month", year, month)); return {"days": []}

    def add_entry(self, exercise_id, minutes, entry_date=None):
        self.calls.append(("add_entry", exercise_id, minutes)); return "77"

    def edit_entry(self, exercise_entry_id, minutes):
        self.calls.append(("edit_entry", exercise_entry_id, minutes))


class FakeWeight:
    def __init__(self):
        self.calls = []

    def update(self, weight_kg, entry_date=None, comment=None):
        self.calls.append(("update", weight_kg, entry_date, comment))

    def get_month(self, year, month):
        self.calls.append(("get_month", year, month)); return {"days": []}


def build_ex(monkeypatch):
    from fatsecret_mcp.tools import exercise as mod
    mcp, fake = FakeMCP(), FakeExercise()
    monkeypatch.setattr(mod, "ExerciseAPI", lambda client: fake)
    mod.register_exercise_tool(mcp, client=object())
    return mcp.tools["fatsecret_exercise"], fake


def build_w(monkeypatch):
    from fatsecret_mcp.tools import weight as mod
    mcp, fake = FakeMCP(), FakeWeight()
    monkeypatch.setattr(mod, "WeightAPI", lambda client: fake)
    mod.register_weight_tool(mcp, client=object())
    return mcp.tools["fatsecret_weight"], fake


def test_exercise_add_requires_id_and_minutes(monkeypatch):
    tool, _ = build_ex(monkeypatch)
    out = tool(action="add")
    assert "exercise_id" in out["error"] and "minutes" in out["error"]


def test_exercise_search_dispatches(monkeypatch):
    tool, fake = build_ex(monkeypatch)
    tool(action="search", query="running")
    assert fake.calls == [("search", "running")]


def test_exercise_unknown_action(monkeypatch):
    tool, _ = build_ex(monkeypatch)
    assert "error" in tool(action="delete")


def test_weight_update_requires_a_weight(monkeypatch):
    tool, _ = build_w(monkeypatch)
    assert "weight_kg" in tool(action="update")["error"]


def test_weight_update_passes_the_comment_through(monkeypatch):
    tool, fake = build_w(monkeypatch)
    tool(action="update", weight_kg=82.4, comment="morning")
    assert fake.calls == [("update", 82.4, None, "morning")]


def test_weight_month_defaults_to_the_current_month(monkeypatch):
    tool, fake = build_w(monkeypatch)
    tool(action="month")
    assert fake.calls[0][0] == "get_month" and fake.calls[0][1] is not None
