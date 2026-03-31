"""MCP tools for food search and nutrition information."""

from typing import Optional
from ..api.base_client import FatSecretClient
from ..api.foods import FoodsAPI
from ..api.recipes import RecipesAPI
from ..utils import get_logger, APIError

logger = get_logger(__name__)


def register_food_tools(mcp, client: Optional[FatSecretClient] = None):
    """
    Register food-related tools with FastMCP server.

    Args:
        mcp: FastMCP server instance
        client: Optional pre-configured FatSecretClient
    """
    # Create API client if not provided
    if client is None:
        client = FatSecretClient()

    foods_api = FoodsAPI(client)
    recipes_api = RecipesAPI(client)

    @mcp.tool()
    def fatsecret_food_search(
        query: str, max_results: int = 50, page: int = 0
    ) -> dict:
        """
        Search for foods by name in the FatSecret database.

        This tool searches the FatSecret food database and returns matching foods
        with basic information. Use fatsecret_food_get to retrieve detailed
        nutrition information for a specific food.

        Args:
            query: Search query (e.g., "apple", "chicken breast", "cheddar cheese")
            max_results: Maximum number of results to return (default: 50, max: 50)
            page: Page number for pagination (default: 0)

        Returns:
            Dictionary containing:
            - foods: List of matching foods with food_id, name, brand, and description
            - total_results: Total number of matching foods
            - max_results: Maximum results per page
            - page_number: Current page number

        Example:
            Search for banana:
            >>> result = fatsecret_food_search(query="banana", max_results=10)
            >>> print(result["foods"][0]["food_name"])
            'Banana'
        """
        try:
            logger.info(f"Searching foods: '{query}'")

            # Validate inputs
            if not query or not query.strip():
                return {
                    "error": "Query cannot be empty",
                    "foods": [],
                    "total_results": 0,
                }

            max_results = min(max(1, max_results), 50)  # Clamp between 1-50
            page = max(0, page)  # Ensure non-negative

            # Perform search
            result = foods_api.search(
                search_expression=query.strip(),
                max_results=max_results,
                page_number=page,
            )

            # Format response
            foods_list = [
                {
                    "food_id": food.food_id,
                    "food_name": food.food_name,
                    "food_type": food.food_type,
                    "brand_name": food.brand_name,
                    "food_description": food.food_description,
                }
                for food in result.foods
            ]

            return {
                "foods": foods_list,
                "total_results": result.total_results,
                "max_results": result.max_results,
                "page_number": result.page_number,
            }

        except APIError as e:
            logger.error(f"API error in food search: {e}")
            return {"error": str(e), "foods": [], "total_results": 0}
        except Exception as e:
            logger.error(f"Unexpected error in food search: {e}")
            return {
                "error": f"Unexpected error: {str(e)}",
                "foods": [],
                "total_results": 0,
            }

    @mcp.tool()
    def fatsecret_food_get(food_id: str) -> dict:  # type: ignore[reportUnusedFunction]
        """
        Get detailed nutrition information for a specific food.

        This tool retrieves comprehensive nutrition facts for a food item,
        including all available serving sizes and their nutritional values.

        Args:
            food_id: FatSecret food ID (obtained from fatsecret_food_search)

        Returns:
            Dictionary containing:
            - food_id: Food identifier
            - food_name: Name of the food
            - brand_name: Brand name (if applicable)
            - food_type: Type of food (Generic, Brand, etc.)
            - servings: List of serving sizes with detailed nutrition facts
              Each serving includes:
              - serving_description: Description of serving size
              - calories: Calories per serving
              - carbohydrate: Carbs in grams
              - protein: Protein in grams
              - fat: Total fat in grams
              - saturated_fat, fiber, sugar, sodium, etc.

        Example:
            Get nutrition facts for a food:
            >>> result = fatsecret_food_get(food_id="12345")
            >>> print(result["food_name"])
            >>> for serving in result["servings"]:
            ...     print(f"{serving['serving_description']}: {serving['calories']} cal")
        """
        try:
            logger.info(f"Getting food details: {food_id}")

            # Validate input
            if not food_id or not food_id.strip():
                return {"error": "food_id cannot be empty"}

            # Get food details
            food = foods_api.get(food_id.strip())

            # Format servings
            servings_list = []
            for serving in food.servings:
                serving_dict = {
                    "serving_id": serving.serving_id,
                    "serving_description": serving.serving_description,
                    "metric_serving_amount": serving.metric_serving_amount,
                    "metric_serving_unit": serving.metric_serving_unit,
                    "calories": serving.calories,
                    "carbohydrate": serving.carbohydrate,
                    "protein": serving.protein,
                    "fat": serving.fat,
                    "saturated_fat": serving.saturated_fat,
                    "polyunsaturated_fat": serving.polyunsaturated_fat,
                    "monounsaturated_fat": serving.monounsaturated_fat,
                    "trans_fat": serving.trans_fat,
                    "cholesterol": serving.cholesterol,
                    "sodium": serving.sodium,
                    "potassium": serving.potassium,
                    "fiber": serving.fiber,
                    "sugar": serving.sugar,
                    "vitamin_a": serving.vitamin_a,
                    "vitamin_c": serving.vitamin_c,
                    "calcium": serving.calcium,
                    "iron": serving.iron,
                }
                servings_list.append(serving_dict)

            return {
                "food_id": food.food_id,
                "food_name": food.food_name,
                "brand_name": food.brand_name,
                "food_type": food.food_type,
                "food_url": food.food_url,
                "servings": servings_list,
            }

        except APIError as e:
            logger.error(f"API error in food get: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in food get: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

    @mcp.tool()
    def fatsecret_food_autocomplete(query: str, max_results: int = 10) -> dict:
        """
        Get autocomplete suggestions for food search.

        This tool provides food name suggestions as you type, useful for
        helping users discover foods or correct spelling.

        Args:
            query: Partial food name (e.g., "chick" -> "chicken breast")
            max_results: Maximum number of suggestions (default: 10)

        Returns:
            Dictionary containing:
            - suggestions: List of food name suggestions
            - count: Number of suggestions returned

        Example:
            Get suggestions:
            >>> result = fatsecret_food_autocomplete(query="chick")
            >>> print(result["suggestions"])
            ['Chicken Breast', 'Chicken Thigh', 'Chickpeas']
        """
        try:
            logger.info(f"Getting autocomplete for: '{query}'")

            # Validate input
            if not query or not query.strip():
                return {"suggestions": [], "count": 0}

            max_results = min(max(1, max_results), 20)  # Clamp between 1-20

            # Get suggestions
            suggestions = foods_api.autocomplete(
                expression=query.strip(), max_results=max_results
            )

            return {"suggestions": suggestions, "count": len(suggestions)}

        except APIError as e:
            logger.error(f"API error in autocomplete: {e}")
            return {"error": str(e), "suggestions": [], "count": 0}
        except Exception as e:
            logger.error(f"Unexpected error in autocomplete: {e}")
            return {
                "error": f"Unexpected error: {str(e)}",
                "suggestions": [],
                "count": 0,
            }

    @mcp.tool()
    def fatsecret_food_search_v3(
        query: str,
        max_results: int = 50,
        page: int = 0,
        region: str = "US",
        language: str = "en",
    ) -> dict:
        """
        Advanced food search with additional filters (v3 API).

        This is an enhanced version of food search with more options.
        For basic searches, use fatsecret_food_search instead.

        Args:
            query: Search query (e.g., "organic milk")
            max_results: Maximum number of results (default: 50)
            page: Page number for pagination (default: 0)
            region: Region code (default: "US")
            language: Language code (default: "en")

        Returns:
            Dictionary containing:
            - foods: List of matching foods
            - total_results: Total number of matches
            - max_results: Results per page
            - page_number: Current page

        Example:
            >>> result = fatsecret_food_search_v3(query="organic banana")
        """
        # For now, this uses the same implementation as v2
        # FatSecret API v3 has more features but requires additional implementation
        return fatsecret_food_search(query=query, max_results=max_results, page=page)

    @mcp.tool()
    def fatsecret_food_barcode_scan(barcode: str) -> dict:
        """
        Lookup food by barcode (UPC/EAN).

        This tool searches for foods by their barcode number.
        Useful for scanning packaged foods.

        Args:
            barcode: Barcode number (UPC or EAN format)
                    Example: "012000161155"

        Returns:
            Dictionary containing:
            - food: Food information if found
            - error: Error message if not found

        Example:
            Scan a barcode:
            >>> result = fatsecret_food_barcode_scan(barcode="012000161155")
            >>> if 'food' in result:
            ...     print(result['food']['food_name'])

        Note:
            Not all foods have barcode data. Generic/unbranded foods typically
            don't have barcodes. Works best with packaged/branded products.
        """
        try:
            logger.info(f"Searching food by barcode: {barcode}")

            if not barcode or not barcode.strip():
                return {"error": "Barcode cannot be empty"}

            # Search using barcode as query
            # FatSecret API doesn't have a dedicated barcode endpoint,
            # but searching by barcode often returns the correct food
            results = foods_api.search(barcode.strip(), max_results=10)

            if not results.foods:
                return {
                    "error": f"No food found with barcode: {barcode}",
                    "suggestion": "Try searching by food name instead",
                }

            # Return first result (most relevant)
            food = results.foods[0]
            return {
                "food": {
                    "food_id": food.food_id,
                    "food_name": food.food_name,
                    "brand_name": food.brand_name,
                    "food_type": food.food_type,
                    "food_description": food.food_description,
                },
                "message": "Use fatsecret_food_get to get full nutrition details",
            }

        except APIError as e:
            logger.error(f"API error in barcode scan: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in barcode scan: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

    @mcp.tool()
    def fatsecret_food_create(
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
    ) -> dict:
        """
        Create a new branded food item in the FatSecret database.

        Use this when a food product is not found in FatSecret and needs
        to be added manually (e.g., local brands, store-specific products).

        Args:
            food_name: Food name excluding brand (e.g., "Instant Oatmeal")
            brand_name: Brand identifier (e.g., "Quaker")
            brand_type: One of: "manufacturer", "restaurant", or "supermarket"
            serving_size: Complete serving description (e.g., "1 packet (43g)")
            calories: Energy content in kcal
            fat: Total fat in grams
            carbohydrate: Total carbohydrates in grams
            protein: Protein in grams
            serving_amount: Numeric serving amount (e.g., 43)
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

        Returns:
            Dictionary containing:
            - food_id: ID of the newly created food
            - message: Confirmation message

        Example:
            Create a local brand product:
            >>> result = fatsecret_food_create(
            ...     food_name="Творог 5%",
            ...     brand_name="Простоквашино",
            ...     brand_type="manufacturer",
            ...     serving_size="100 г",
            ...     calories=121,
            ...     fat=5.0,
            ...     carbohydrate=3.0,
            ...     protein=16.0,
            ... )
            >>> print(result["food_id"])
        """
        try:
            logger.info(f"Creating food: '{brand_name} {food_name}'")

            # Validate brand_type
            valid_brand_types = ("manufacturer", "restaurant", "supermarket")
            if brand_type not in valid_brand_types:
                return {
                    "error": f"brand_type must be one of: {', '.join(valid_brand_types)}",
                }

            # Validate required fields
            if not food_name or not food_name.strip():
                return {"error": "food_name cannot be empty"}
            if not brand_name or not brand_name.strip():
                return {"error": "brand_name cannot be empty"}
            if not serving_size or not serving_size.strip():
                return {"error": "serving_size cannot be empty"}

            food_id = foods_api.create(
                food_name=food_name.strip(),
                brand_name=brand_name.strip(),
                brand_type=brand_type,
                serving_size=serving_size.strip(),
                calories=calories,
                fat=fat,
                carbohydrate=carbohydrate,
                protein=protein,
                serving_amount=serving_amount,
                serving_amount_unit=serving_amount_unit,
                saturated_fat=saturated_fat,
                polyunsaturated_fat=polyunsaturated_fat,
                monounsaturated_fat=monounsaturated_fat,
                trans_fat=trans_fat,
                cholesterol=cholesterol,
                sodium=sodium,
                potassium=potassium,
                fiber=fiber,
                sugar=sugar,
                added_sugars=added_sugars,
                vitamin_d=vitamin_d,
                vitamin_a=vitamin_a,
                vitamin_c=vitamin_c,
                calcium=calcium,
                iron=iron,
            )

            return {
                "food_id": food_id,
                "message": f"Food '{brand_name} {food_name}' created successfully",
            }

        except APIError as e:
            logger.error(f"API error in food create: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in food create: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

    @mcp.tool()
    def fatsecret_recipe_search(query: str, max_results: int = 50, page: int = 0) -> dict:
        """
        Search for recipes by name or ingredients.

        This tool searches the FatSecret recipe database for meal ideas,
        cooking instructions, and nutritional information.

        Args:
            query: Search query (e.g., "chocolate cake", "pasta carbonara", "chicken")
            max_results: Maximum number of results (default: 50)
            page: Page number for pagination (default: 0)

        Returns:
            Dictionary containing:
            - recipes: List of matching recipes with:
              - recipe_id: Recipe identifier
              - recipe_name: Name of the recipe
              - recipe_description: Brief description
              - recipe_url: Link to full recipe
              - recipe_image: Image URL
            - total_results: Total number of matching recipes
            - max_results: Results per page
            - page_number: Current page

        Example:
            Search for chocolate cake recipes:
            >>> result = fatsecret_recipe_search(query="chocolate cake")
            >>> for recipe in result['recipes']:
            ...     print(f"{recipe['recipe_name']} - {recipe['recipe_url']}")
        """
        try:
            logger.info(f"Searching recipes: '{query}'")

            if not query or not query.strip():
                return {"error": "Query cannot be empty", "recipes": [], "total_results": 0}

            max_results = min(max(1, max_results), 50)
            page = max(0, page)

            result = recipes_api.search(query.strip(), max_results, page)

            recipes_list = [
                {
                    "recipe_id": recipe.recipe_id,
                    "recipe_name": recipe.recipe_name,
                    "recipe_description": recipe.recipe_description,
                    "recipe_url": recipe.recipe_url,
                    "recipe_image": recipe.recipe_image,
                }
                for recipe in result.recipes
            ]

            return {
                "recipes": recipes_list,
                "total_results": result.total_results,
                "max_results": result.max_results,
                "page_number": result.page_number,
            }

        except APIError as e:
            logger.error(f"API error in recipe search: {e}")
            return {"error": str(e), "recipes": [], "total_results": 0}
        except Exception as e:
            logger.error(f"Unexpected error in recipe search: {e}")
            return {"error": f"Unexpected error: {str(e)}", "recipes": [], "total_results": 0}

    @mcp.tool()
    def fatsecret_recipe_get(recipe_id: str) -> dict:
        """
        Get detailed recipe information including ingredients and cooking instructions.

        This tool retrieves complete recipe details with nutrition facts per serving,
        ingredients list, and step-by-step directions.

        Args:
            recipe_id: FatSecret recipe ID (from fatsecret_recipe_search)

        Returns:
            Dictionary containing:
            - recipe_id: Recipe identifier
            - recipe_name: Recipe name
            - recipe_description: Description
            - recipe_url: Link to full recipe
            - recipe_image: Image URL
            - cooking_time_min: Cooking time in minutes
            - number_of_servings: Number of servings
            - calories_per_serving: Calories per serving
            - carbohydrate_per_serving: Carbs per serving (g)
            - protein_per_serving: Protein per serving (g)
            - fat_per_serving: Fat per serving (g)
            - directions: List of cooking steps

        Example:
            Get recipe details:
            >>> result = fatsecret_recipe_get(recipe_id="12345")
            >>> print(f"Recipe: {result['recipe_name']}")
            >>> print(f"Servings: {result['number_of_servings']}")
            >>> print(f"Calories per serving: {result['calories_per_serving']}")
            >>> print("\\nDirections:")
            >>> for i, step in enumerate(result['directions'], 1):
            ...     print(f"{i}. {step}")
        """
        try:
            logger.info(f"Getting recipe details: {recipe_id}")

            if not recipe_id or not recipe_id.strip():
                return {"error": "recipe_id cannot be empty"}

            recipe = recipes_api.get(recipe_id.strip())

            return {
                "recipe_id": recipe.recipe_id,
                "recipe_name": recipe.recipe_name,
                "recipe_description": recipe.recipe_description,
                "recipe_url": recipe.recipe_url,
                "recipe_image": recipe.recipe_image,
                "cooking_time_min": recipe.cooking_time_min,
                "number_of_servings": recipe.number_of_servings,
                "calories_per_serving": recipe.calories_per_serving,
                "carbohydrate_per_serving": recipe.carbohydrate_per_serving,
                "protein_per_serving": recipe.protein_per_serving,
                "fat_per_serving": recipe.fat_per_serving,
                "directions": recipe.directions,
            }

        except APIError as e:
            logger.error(f"API error in recipe get: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in recipe get: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

    logger.info("Registered food search and recipe tools")
