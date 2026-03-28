"""Foods API client for FatSecret Platform API."""

from typing import Optional, List, Dict, Any
from ..utils import get_logger
from .base_client import FatSecretClient
from ..models.food import Food, FoodSearchResult, ServingInfo

logger = get_logger(__name__)


class FoodsAPI:
    """Client for FatSecret Foods API."""

    def __init__(self, client: FatSecretClient):
        """
        Initialize Foods API client.

        Args:
            client: Authenticated FatSecret client
        """
        self.client = client

    def search(
        self,
        search_expression: str,
        max_results: int = 50,
        page_number: int = 0,
    ) -> FoodSearchResult:
        """
        Search for foods by name.

        Args:
            search_expression: Search query (e.g., "apple", "chicken breast")
            max_results: Maximum number of results (default 50)
            page_number: Page number for pagination (default 0)

        Returns:
            FoodSearchResult with matching foods

        Example:
            >>> api = FoodsAPI(client)
            >>> results = api.search("banana")
            >>> print(results.foods[0].food_name)
            'Banana'
        """
        logger.info(f"Searching foods: '{search_expression}'")

        response = self.client.get(
            "foods.search",
            search_expression=search_expression,
            max_results=max_results,
            page_number=page_number,
        )

        # Parse response
        foods_data = response.get("foods", {})
        food_list = foods_data.get("food", [])

        # Ensure food_list is a list
        if isinstance(food_list, dict):
            food_list = [food_list]

        # Convert to Food objects
        foods = []
        for food_data in food_list:
            food = Food(
                food_id=str(food_data.get("food_id", "")),
                food_name=food_data.get("food_name", ""),
                food_type=food_data.get("food_type"),
                food_url=food_data.get("food_url"),
                food_description=food_data.get("food_description"),
                brand_name=food_data.get("brand_name"),
            )
            foods.append(food)

        result = FoodSearchResult(
            foods=foods,
            total_results=int(foods_data.get("total_results", len(foods))),
            max_results=int(foods_data.get("max_results", max_results)),
            page_number=int(foods_data.get("page_number", page_number)),
        )

        logger.info(f"Found {len(foods)} foods")
        return result

    def get(self, food_id: str) -> Food:
        """
        Get detailed food information including nutrition facts.

        Args:
            food_id: FatSecret food ID

        Returns:
            Food object with detailed nutrition information

        Example:
            >>> api = FoodsAPI(client)
            >>> food = api.get("12345")
            >>> print(food.food_name)
            >>> for serving in food.servings:
            ...     print(f"{serving.serving_description}: {serving.calories} cal")
        """
        logger.info(f"Getting food details: {food_id}")

        response = self.client.get("food.get.v2", food_id=food_id)

        # Parse response
        food_data = response.get("food", {})

        # Parse servings
        servings = []
        servings_data = food_data.get("servings", {}).get("serving", [])

        # Ensure servings_data is a list
        if isinstance(servings_data, dict):
            servings_data = [servings_data]

        for serving_data in servings_data:
            serving = ServingInfo(
                serving_id=str(serving_data.get("serving_id", "")),
                serving_description=serving_data.get("serving_description", ""),
                serving_url=serving_data.get("serving_url"),
                metric_serving_amount=self._parse_float(
                    serving_data.get("metric_serving_amount")
                ),
                metric_serving_unit=serving_data.get("metric_serving_unit"),
                number_of_units=self._parse_float(serving_data.get("number_of_units")),
                measurement_description=serving_data.get("measurement_description"),
                calories=self._parse_float(serving_data.get("calories")),
                carbohydrate=self._parse_float(serving_data.get("carbohydrate")),
                protein=self._parse_float(serving_data.get("protein")),
                fat=self._parse_float(serving_data.get("fat")),
                saturated_fat=self._parse_float(serving_data.get("saturated_fat")),
                polyunsaturated_fat=self._parse_float(
                    serving_data.get("polyunsaturated_fat")
                ),
                monounsaturated_fat=self._parse_float(
                    serving_data.get("monounsaturated_fat")
                ),
                trans_fat=self._parse_float(serving_data.get("trans_fat")),
                cholesterol=self._parse_float(serving_data.get("cholesterol")),
                sodium=self._parse_float(serving_data.get("sodium")),
                potassium=self._parse_float(serving_data.get("potassium")),
                fiber=self._parse_float(serving_data.get("fiber")),
                sugar=self._parse_float(serving_data.get("sugar")),
                vitamin_a=self._parse_float(serving_data.get("vitamin_a")),
                vitamin_c=self._parse_float(serving_data.get("vitamin_c")),
                calcium=self._parse_float(serving_data.get("calcium")),
                iron=self._parse_float(serving_data.get("iron")),
            )
            servings.append(serving)

        food = Food(
            food_id=str(food_data.get("food_id", "")),
            food_name=food_data.get("food_name", ""),
            food_type=food_data.get("food_type"),
            food_url=food_data.get("food_url"),
            food_description=food_data.get("food_description"),
            brand_name=food_data.get("brand_name"),
            servings=servings,
        )

        logger.info(f"Retrieved food: {food.food_name} with {len(servings)} servings")
        return food

    def autocomplete(self, expression: str, max_results: int = 10) -> List[str]:
        """
        Get autocomplete suggestions for food search.

        Args:
            expression: Partial search query
            max_results: Maximum number of suggestions

        Returns:
            List of food name suggestions

        Example:
            >>> api = FoodsAPI(client)
            >>> suggestions = api.autocomplete("chick")
            >>> print(suggestions)
            ['Chicken Breast', 'Chicken Thigh', 'Chickpeas']
        """
        logger.info(f"Getting autocomplete for: '{expression}'")

        response = self.client.get(
            "foods.autocomplete", expression=expression, max_results=max_results
        )

        suggestions_data = response.get("suggestions", {})
        suggestions = suggestions_data.get("suggestion", [])

        # Ensure suggestions is a list
        if isinstance(suggestions, str):
            suggestions = [suggestions]

        logger.info(f"Found {len(suggestions)} suggestions")
        return suggestions

    @staticmethod
    def _parse_float(value: Any) -> Optional[float]:
        """Parse value to float, return None if invalid."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
