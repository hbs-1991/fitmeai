"""fatsecret_food: one tool, six actions. Tests drive a fake API layer — no network."""
import pytest

from fatsecret_mcp.tools.dispatch import ActionError, require


class FakeMCP:
    """Captures what register_*_tool registers, so tests can call the function
    directly instead of standing up a real FastMCP server."""
    def __init__(self):
        self.tools = {}

    def tool(self, *a, **kw):
        def deco(fn):
            self.tools[fn.__name__] = fn
            return fn
        return deco


class FakeFoods:
    def __init__(self):
        self.calls = []

    def search(self, search_expression, max_results=50, page_number=0):
        self.calls.append(("search", search_expression, max_results, page_number))
        return {"foods": [{"food_id": "1641", "food_name": search_expression}]}

    def get(self, food_id):
        self.calls.append(("get", food_id))
        return {"food_id": food_id, "servings": [{"serving_id": "50321",
                                                  "serving_description": "100 g"}]}

    def find_id_for_barcode(self, barcode):
        self.calls.append(("barcode", barcode))
        return "1641" if barcode == "0012000161155" else None

    def create(self, food_name, brand_name, brand_type, serving_size,
               calories, fat, carbohydrate, protein, **extra):
        """Mirrors the REAL FoodsAPI.create signature on purpose: brand_name and
        brand_type are required positional arguments there, and a fake that swallowed
        everything into **kwargs would let a call that cannot work in production pass
        its unit test. It also returns a bare str, as the real one does."""
        self.calls.append(("create", food_name, brand_name, brand_type, extra))
        return "9911"


def build(monkeypatch, foods=None):
    from fatsecret_mcp.tools import food as food_mod
    mcp, fake = FakeMCP(), foods or FakeFoods()
    monkeypatch.setattr(food_mod, "FoodsAPI", lambda client: fake)
    monkeypatch.setattr(food_mod, "RecipesAPI", lambda client: fake)
    food_mod.register_food_tool(mcp, client=object())
    return mcp.tools["fatsecret_food"], fake


def test_require_names_every_missing_parameter_at_once():
    with pytest.raises(ActionError) as e:
        require({"a": "x", "b": None, "c": ""}, "add", "a", "b", "c")
    assert "b" in str(e.value) and "c" in str(e.value) and "add" in str(e.value)


def test_search_dispatches_to_the_api(monkeypatch):
    tool, fake = build(monkeypatch)
    out = tool(action="search", query="banana")
    assert fake.calls[0][:2] == ("search", "banana")
    assert "error" not in out


def test_an_unknown_action_returns_an_error_listing_the_valid_ones(monkeypatch):
    tool, _ = build(monkeypatch)
    out = tool(action="frobnicate")
    assert "frobnicate" in out["error"] and "search" in out["error"]


def test_a_missing_required_parameter_is_an_error_not_an_exception(monkeypatch):
    """P5: the model must get a correctable message, not a dead turn."""
    tool, _ = build(monkeypatch)
    out = tool(action="get")
    assert "food_id" in out["error"]


def test_barcode_uses_the_real_endpoint_then_fetches_the_food(monkeypatch):
    """The old fatsecret_food_barcode_scan just text-searched the digits
    (foods_tools.py:315) — it was never a barcode lookup."""
    tool, fake = build(monkeypatch)
    out = tool(action="barcode", barcode="0012000161155")
    assert ("barcode", "0012000161155") in fake.calls
    assert out["food_id"] == "1641"


def test_barcode_pads_a_short_upc_to_gtin13(monkeypatch):
    """FatSecret's find_id_for_barcode requires GTIN-13; a 12-digit UPC needs a
    leading zero or the lookup silently misses."""
    tool, fake = build(monkeypatch)
    tool(action="barcode", barcode="012000161155")
    assert ("barcode", "0012000161155") in fake.calls


def test_barcode_not_found_is_a_clean_message(monkeypatch):
    tool, _ = build(monkeypatch)
    out = tool(action="barcode", barcode="9999999999999")
    assert "error" in out and "9999999999999" in out["error"]


def test_the_dropped_v3_and_autocomplete_actions_are_gone(monkeypatch):
    tool, _ = build(monkeypatch)
    for dead in ("search_v3", "autocomplete"):
        assert "error" in tool(action=dead)


MACROS = {"serving_size": "1 порция", "calories": 320, "fat": 24,
          "carbohydrate": 3, "protein": 22}


def test_create_supplies_the_brand_fields_the_api_requires(monkeypatch):
    """FoodsAPI.create takes brand_name and brand_type as REQUIRED arguments, but the
    tool's documented contract asks only for the macros. Without a default here, every
    docstring-conformant call dies on a TypeError — and the nutrition-log skill routes
    repeat homemade dishes straight to this action."""
    tool, fake = build(monkeypatch)
    out = tool(action="create", query="Омлет", nutrition=MACROS)
    assert "error" not in out, out
    _, name, brand, brand_type, _extra = fake.calls[0]
    assert (name, brand, brand_type) == ("Омлет", "Homemade", "manufacturer")


def test_create_returns_a_dict_not_the_bare_food_id(monkeypatch):
    """The tool is declared -> dict and FatSecret's create returns a bare string.
    FastMCP rejects a non-dict payload as a protocol error that escapes @guard — an
    infrastructure failure the model cannot correct, which is the whole thing the
    error-dict convention exists to prevent."""
    out = build(monkeypatch)[0](action="create", query="Омлет", nutrition=MACROS)
    assert out == {"food_id": "9911"}


def test_create_passes_an_explicit_brand_through_and_normalizes_its_type(monkeypatch):
    tool, fake = build(monkeypatch)
    out = tool(action="create", query="Oatmeal",
               nutrition={**MACROS, "brand_name": "Quaker",
                          "brand_type": "Manufacturer"})
    assert out == {"food_id": "9911"}
    assert fake.calls[0][2:4] == ("Quaker", "manufacturer")


def test_create_rejects_a_brand_type_the_api_does_not_accept(monkeypatch):
    tool, _ = build(monkeypatch)
    out = tool(action="create", query="x",
               nutrition={**MACROS, "brand_type": "homemade"})
    assert "homemade" in out["error"] and "manufacturer" in out["error"]


def test_create_does_not_mutate_the_callers_nutrition_dict(monkeypatch):
    """The brand fields are popped before **-forwarding; popping them out of the
    caller's own dict would corrupt a retry."""
    tool, _ = build(monkeypatch)
    payload = {**MACROS, "brand_name": "Quaker"}
    tool(action="create", query="x", nutrition=payload)
    assert payload["brand_name"] == "Quaker"
