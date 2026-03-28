"""Recipes API client for FatSecret Platform API."""

from typing import Optional, List
from ..utils import get_logger
from .base_client import FatSecretClient
from ..models.recipe import Recipe, RecipeSearchResult

logger = get_logger(__name__)


class RecipesAPI:
    """Client for FatSecret Recipes API."""

    def __init__(self, client: FatSecretClient):
        """
        Initialize Recipes API client.

        Args:
            client: FatSecret client (public API, no auth required)
        """
        self.client = client

    def search(
        self,
        search_expression: str,
        max_results: int = 50,
        page_number: int = 0,
    ) -> RecipeSearchResult:
        """
        Search for recipes.

        Args:
            search_expression: Search query (e.g., "chocolate cake", "pasta")
            max_results: Maximum number of results (default 50)
            page_number: Page number for pagination (default 0)

        Returns:
            RecipeSearchResult with matching recipes

        Example:
            >>> api = RecipesAPI(client)
            >>> results = api.search("chocolate cake")
            >>> for recipe in results.recipes:
            ...     print(recipe.recipe_name)
        """
        logger.info(f"Searching recipes: '{search_expression}'")

        response = self.client.get(
            "recipes.search",
            search_expression=search_expression,
            max_results=max_results,
            page_number=page_number,
        )

        # Parse response
        recipes_data = response.get("recipes", {})
        recipe_list = recipes_data.get("recipe", [])

        # Ensure it's a list
        if isinstance(recipe_list, dict):
            recipe_list = [recipe_list]

        # Convert to Recipe objects
        recipes = []
        for recipe_data in recipe_list:
            recipe = Recipe(
                recipe_id=str(recipe_data.get("recipe_id", "")),
                recipe_name=recipe_data.get("recipe_name", ""),
                recipe_description=recipe_data.get("recipe_description"),
                recipe_url=recipe_data.get("recipe_url"),
                recipe_image=recipe_data.get("recipe_image"),
            )
            recipes.append(recipe)

        result = RecipeSearchResult(
            recipes=recipes,
            total_results=int(recipes_data.get("total_results", len(recipes))),
            max_results=int(recipes_data.get("max_results", max_results)),
            page_number=int(recipes_data.get("page_number", page_number)),
        )

        logger.info(f"Found {len(recipes)} recipes")
        return result

    def get(self, recipe_id: str) -> Recipe:
        """
        Get detailed recipe information.

        Args:
            recipe_id: FatSecret recipe ID

        Returns:
            Recipe object with full details

        Example:
            >>> api = RecipesAPI(client)
            >>> recipe = api.get("12345")
            >>> print(recipe.recipe_name)
            >>> print(f"Servings: {recipe.number_of_servings}")
            >>> print(f"Calories per serving: {recipe.calories_per_serving}")
        """
        logger.info(f"Getting recipe details: {recipe_id}")

        response = self.client.get("recipe.get", recipe_id=recipe_id)

        # Parse response
        recipe_data = response.get("recipe", {})

        # Parse directions
        directions = []
        directions_data = recipe_data.get("directions", {})
        if isinstance(directions_data, dict):
            direction_list = directions_data.get("direction", [])
            if isinstance(direction_list, dict):
                direction_list = [direction_list]
            for d in direction_list:
                if isinstance(d, dict):
                    directions.append(d.get("direction_description", ""))
                else:
                    directions.append(str(d))

        # Parse serving info
        serving_sizes = recipe_data.get("serving_sizes", {})
        serving = serving_sizes.get("serving", {}) if serving_sizes else {}

        recipe = Recipe(
            recipe_id=str(recipe_data.get("recipe_id", "")),
            recipe_name=recipe_data.get("recipe_name", ""),
            recipe_description=recipe_data.get("recipe_description"),
            recipe_url=recipe_data.get("recipe_url"),
            recipe_image=recipe_data.get("recipe_images", {}).get("recipe_image"),
            cooking_time_min=self._parse_int(recipe_data.get("cooking_time_min")),
            number_of_servings=self._parse_int(recipe_data.get("number_of_servings")),
            calories_per_serving=self._parse_float(serving.get("calories")),
            carbohydrate_per_serving=self._parse_float(serving.get("carbohydrate")),
            protein_per_serving=self._parse_float(serving.get("protein")),
            fat_per_serving=self._parse_float(serving.get("fat")),
            directions=directions,
        )

        logger.info(f"Retrieved recipe: {recipe.recipe_name}")
        return recipe

    @staticmethod
    def _parse_int(value) -> Optional[int]:
        """Parse value to int, return None if invalid."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_float(value) -> Optional[float]:
        """Parse value to float, return None if invalid."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
