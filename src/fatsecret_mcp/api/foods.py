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

    def create(
        self,
        food_name: str,
        brand_name: str,
        brand_type: str,
        serving_size: str,
        calories: float,
        fat: float,
        carbohydrate: float,
        protein: float,
        serving_amount: Optional[float] = None,
        serving_amount_unit: Optional[str] = None,
        saturated_fat: Optional[float] = None,
        polyunsaturated_fat: Optional[float] = None,
        monounsaturated_fat: Optional[float] = None,
        trans_fat: Optional[float] = None,
        cholesterol: Optional[float] = None,
        sodium: Optional[float] = None,
        potassium: Optional[float] = None,
        fiber: Optional[float] = None,
        sugar: Optional[float] = None,
        added_sugars: Optional[float] = None,
        vitamin_d: Optional[float] = None,
        vitamin_a: Optional[float] = None,
        vitamin_c: Optional[float] = None,
        calcium: Optional[float] = None,
        iron: Optional[float] = None,
        region: Optional[str] = None,
        language: Optional[str] = None,
    ) -> str:
        """
        Create a new branded food item in FatSecret.

        Args:
            food_name: Food name excluding brand (e.g., "Instant Oatmeal")
            brand_name: Brand identifier (e.g., "Quaker")
            brand_type: One of "manufacturer", "restaurant", or "supermarket"
            serving_size: Complete serving description (e.g., "1 packet (43g)")
            calories: Energy content in kcal
            fat: Total fat in grams
            carbohydrate: Total carbohydrates in grams
            protein: Protein in grams
            serving_amount: Numeric serving amount
            serving_amount_unit: Unit for serving_amount (e.g., "g", "ml")
            saturated_fat: Saturated fat in grams
            polyunsaturated_fat: Polyunsaturated fat in grams
            monounsaturated_fat: Monounsaturated fat in grams
            trans_fat: Trans fat in grams
            cholesterol: Cholesterol in mg
            sodium: Sodium in mg
            potassium: Potassium in mg
            fiber: Dietary fiber in grams
            sugar: Sugar in grams
            added_sugars: Added sugars in grams
            vitamin_d: Vitamin D in mcg
            vitamin_a: Vitamin A in mcg RE
            vitamin_c: Vitamin C in mg
            calcium: Calcium in mg
            iron: Iron in mg
            region: Region code (e.g., "US")
            language: Language code (e.g., "en")

        Returns:
            food_id of the newly created food
        """
        logger.info(f"Creating food: '{brand_name} {food_name}'")

        params: Dict[str, Any] = {
            "food_name": food_name,
            "brand_name": brand_name,
            "brand_type": brand_type,
            "serving_size": serving_size,
            "calories": str(calories),
            "fat": str(fat),
            "carbohydrate": str(carbohydrate),
            "protein": str(protein),
        }

        optional_fields = {
            "serving_amount": serving_amount,
            "serving_amount_unit": serving_amount_unit,
            "saturated_fat": saturated_fat,
            "polyunsaturated_fat": polyunsaturated_fat,
            "monounsaturated_fat": monounsaturated_fat,
            "trans_fat": trans_fat,
            "cholesterol": cholesterol,
            "sodium": sodium,
            "potassium": potassium,
            "fiber": fiber,
            "sugar": sugar,
            "added_sugars": added_sugars,
            "vitamin_d": vitamin_d,
            "vitamin_a": vitamin_a,
            "vitamin_c": vitamin_c,
            "calcium": calcium,
            "iron": iron,
            "region": region,
            "language": language,
        }

        for key, value in optional_fields.items():
            if value is not None:
                params[key] = str(value)

        response = self.client.post("food.create.v2", require_auth=False, **params)

        food_id = str(response.get("food_id", {}).get("value", ""))
        logger.info(f"Created food with ID: {food_id}")
        return food_id

    @staticmethod
    def _parse_float(value: Any) -> Optional[float]:
        """Parse value to float, return None if invalid."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
