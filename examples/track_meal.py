"""
Example: Track meals using the FatSecret MCP Server.

This example demonstrates how to add foods to your diary.
Requires OAuth authentication (run setup_oauth.py first).
"""

import sys
import os
from datetime import date

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.fatsecret_mcp.auth import OAuthManager
from src.fatsecret_mcp.api.base_client import FatSecretClient
from src.fatsecret_mcp.api.foods import FoodsAPI
from src.fatsecret_mcp.api.food_diary import FoodDiaryAPI


def main():
    """Example: Track a meal in food diary."""

    # Get OAuth token
    oauth = OAuthManager()
    access_token = oauth.get_valid_access_token()

    if not access_token:
        print("\n❌ Authentication required!")
        print("Please run: python setup_oauth.py")
        sys.exit(1)

    # Create authenticated client
    client = FatSecretClient(access_token=access_token)
    foods_api = FoodsAPI(client)
    diary_api = FoodDiaryAPI(client)

    today = date.today().strftime("%Y-%m-%d")

    print("=" * 60)
    print("Example: Track Breakfast")
    print("=" * 60)

    # Example 1: Search for a food
    print("\n1. Searching for 'scrambled eggs'...")
    results = foods_api.search("scrambled eggs", max_results=1)

    if not results.foods:
        print("No foods found!")
        return

    food = results.foods[0]
    print(f"   Found: {food.food_name}")

    # Get detailed nutrition info
    print("\n2. Getting nutrition details...")
    food_details = foods_api.get(food.food_id)

    if not food_details.servings:
        print("No serving information available!")
        return

    serving = food_details.servings[0]
    print(f"   Serving: {serving.serving_description}")
    print(f"   Calories: {serving.calories} cal")
    print(f"   Protein: {serving.protein}g, Carbs: {serving.carbohydrate}g, Fat: {serving.fat}g")

    # Add to diary
    print("\n3. Adding to breakfast diary...")
    entry_id = diary_api.add_entry(
        food_id=food.food_id,
        serving_id=serving.serving_id,
        meal="breakfast",
        number_of_units=2.0,  # 2 servings
        entry_date=today,
    )
    print(f"   ✅ Added to diary! Entry ID: {entry_id}")

    # View today's diary
    print("\n4. Viewing today's diary...")
    day = diary_api.get_entries(today)

    print(f"\n   📅 Diary for {day.date}")
    print(f"   Total Calories: {day.total_calories:.0f} cal")
    print(f"   Protein: {day.total_protein:.1f}g")
    print(f"   Carbs: {day.total_carbohydrate:.1f}g")
    print(f"   Fat: {day.total_fat:.1f}g")
    print(f"\n   Entries ({len(day.entries)}):")

    for entry in day.entries:
        print(f"   • {entry.food_entry_name} ({entry.meal})")
        print(f"     {entry.number_of_units} serving(s) - {entry.calories:.0f} cal")

    # Cleanup: Delete the entry we just added
    print("\n5. Cleaning up (deleting test entry)...")
    diary_api.delete_entry(entry_id)
    print("   ✅ Test entry deleted")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
