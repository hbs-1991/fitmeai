"""
Example: Search for foods using the FatSecret MCP Server.

This example demonstrates how to search for foods and retrieve nutrition information.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.fatsecret_mcp.api.base_client import FatSecretClient
from src.fatsecret_mcp.api.foods import FoodsAPI


def main():
    """Example: Search foods and get nutrition facts."""

    # Create client (will use client credentials OAuth)
    client = FatSecretClient()
    foods_api = FoodsAPI(client)

    # Example 1: Search for foods
    print("=" * 60)
    print("Example 1: Search for 'banana'")
    print("=" * 60)

    results = foods_api.search("banana", max_results=5)
    print(f"\nFound {results.total_results} results, showing {len(results.foods)}:\n")

    for i, food in enumerate(results.foods, 1):
        print(f"{i}. {food.food_name}")
        if food.brand_name:
            print(f"   Brand: {food.brand_name}")
        print(f"   ID: {food.food_id}")
        print(f"   Type: {food.food_type}")
        print()

    # Example 2: Get detailed nutrition info
    if results.foods:
        food_id = results.foods[0].food_id
        print("=" * 60)
        print(f"Example 2: Get nutrition facts for '{results.foods[0].food_name}'")
        print("=" * 60)

        food = foods_api.get(food_id)
        print(f"\nFood: {food.food_name}")
        if food.brand_name:
            print(f"Brand: {food.brand_name}")
        print(f"\nServings ({len(food.servings)}):\n")

        for serving in food.servings[:3]:  # Show first 3 servings
            print(f"  • {serving.serving_description}")
            print(f"    Calories: {serving.calories or 'N/A'} cal")
            print(f"    Protein: {serving.protein or 'N/A'} g")
            print(f"    Carbs: {serving.carbohydrate or 'N/A'} g")
            print(f"    Fat: {serving.fat or 'N/A'} g")
            print()

    # Example 3: Autocomplete
    print("=" * 60)
    print("Example 3: Autocomplete for 'chick'")
    print("=" * 60)

    suggestions = foods_api.autocomplete("chick", max_results=5)
    print(f"\nSuggestions ({len(suggestions)}):\n")
    for suggestion in suggestions:
        print(f"  • {suggestion}")


if __name__ == "__main__":
    main()
