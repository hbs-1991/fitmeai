"""fatsecret_food — food and recipe lookup, one tool, six actions."""

from __future__ import annotations

from ..api.foods import FoodsAPI
from ..api.recipes import RecipesAPI
from ..utils import get_logger
from .dispatch import ActionError, guard, require, unknown

logger = get_logger(__name__)

ACTIONS = ("search", "get", "barcode", "create", "recipe_search", "recipe_get")
BRAND_TYPES = ("manufacturer", "restaurant", "supermarket")


def _dump(value):
    """The API layer returns pydantic models (`FoodsAPI.get` → `Food`,
    models/food.py:58); MCP needs plain JSON-able data. model_dump() replaces the
    hand-written 25-line serializer the old foods_tools.py carried at lines 150-183."""
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [_dump(v) for v in value]
    return value


def register_food_tool(mcp, client) -> None:
    foods = FoodsAPI(client)
    recipes = RecipesAPI(client)

    @mcp.tool()
    @guard
    def fatsecret_food(
        action: str,
        query: str | None = None,
        food_id: str | None = None,
        barcode: str | None = None,
        recipe_id: str | None = None,
        max_results: int = 20,
        page: int = 0,
        nutrition: dict | None = None,
    ) -> dict:
        """Look up foods and recipes in the FatSecret database.

        Actions:
          search        — find foods by name. Requires: query.
          get           — full nutrition and the serving list for one food.
                          Requires: food_id. Call this before logging: the serving
                          list is where serving_id comes from.
          barcode       — find a food by its GTIN/UPC/EAN digits. Requires: barcode.
          create        — define a custom food. Requires: query (the food name) and
                          nutrition, an object with serving_size, calories, fat,
                          carbohydrate, protein. Optional inside nutrition:
                          brand_name (default "Homemade"), brand_type
                          (manufacturer|restaurant|supermarket), extra nutrients.
          recipe_search — find recipes by name. Requires: query.
          recipe_get    — full recipe with ingredients. Requires: recipe_id.

        Returns the API payload, or {"error": "..."} — never raises.
        Serving semantics for logging are covered by the nutrition-log skill.
        """
        params = locals()
        if action == "search":
            (q,) = require(params, action, "query")
            return {"foods": _dump(foods.search(q, max_results=max_results,
                                                page_number=page))}
        if action == "get":
            (fid,) = require(params, action, "food_id")
            return _dump(foods.get(fid))
        if action == "barcode":
            (code,) = require(params, action, "barcode")
            code = code.strip().zfill(13)
            found = foods.find_id_for_barcode(code)
            if not found:
                return {"error": f"no food found for barcode {code}; it may be an "
                                 f"unbranded item, or not in the FatSecret database"}
            return _dump(foods.get(found))
        if action == "create":
            name, n = require(params, action, "query", "nutrition")
            n = dict(n)                      # never mutate the caller's payload
            for field in ("serving_size", "calories", "fat", "carbohydrate", "protein"):
                if n.get(field) is None:
                    raise ActionError(f"action='create' needs nutrition.{field}")
            # brand_name/brand_type are required by FoodsAPI.create but meaningless for
            # the homemade dishes this action actually gets used for, so they default.
            brand_name = n.pop("brand_name", None) or "Homemade"
            brand_type = (n.pop("brand_type", None) or "manufacturer").lower()
            if brand_type not in BRAND_TYPES:
                raise ActionError(f"brand_type {brand_type!r} is not valid; use one "
                                  f"of: {', '.join(BRAND_TYPES)}")
            # create returns a bare food_id string; the tool is declared -> dict, and
            # FastMCP rejects a non-dict payload as a protocol error that escapes guard.
            return {"food_id": foods.create(food_name=name, brand_name=brand_name,
                                            brand_type=brand_type, **n)}
        if action == "recipe_search":
            (q,) = require(params, action, "query")
            return {"recipes": _dump(recipes.search(q, max_results=max_results,
                                                    page_number=page))}
        if action == "recipe_get":
            (rid,) = require(params, action, "recipe_id")
            return _dump(recipes.get(rid))
        return unknown(action, ACTIONS)

    logger.info("registered fatsecret_food")
