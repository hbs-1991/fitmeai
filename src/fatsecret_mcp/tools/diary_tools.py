"""MCP tools for food diary tracking."""

from typing import Optional
from datetime import date
from ..api.base_client import FatSecretClient
from ..api.food_diary import FoodDiaryAPI
from ..utils import get_logger, APIError

logger = get_logger(__name__)


def register_diary_tools(mcp, client: FatSecretClient):
    """
    Register food diary tools with FastMCP server.

    Args:
        mcp: FastMCP server instance
        client: Authenticated FatSecretClient with user access token
    """
    diary_api = FoodDiaryAPI(client)

    @mcp.tool()
    def fatsecret_diary_get_entries(entry_date: Optional[str] = None) -> dict:
        """
        Get all food diary entries for a specific date.

        This tool retrieves all foods logged in your food diary for a given date,
        including nutritional totals for the day.

        Args:
            entry_date: Date in YYYY-MM-DD format (default: today)
                       Example: "2026-02-03"

        Returns:
            Dictionary containing:
            - date: Date of entries
            - entries: List of food entries with details (meal, food name, servings, nutrition)
            - total_calories: Total calories for the day
            - total_carbohydrate: Total carbs in grams
            - total_protein: Total protein in grams
            - total_fat: Total fat in grams

        Example:
            Get today's entries:
            >>> result = fatsecret_diary_get_entries()
            >>> print(f"Total calories: {result['total_calories']}")

            Get specific date:
            >>> result = fatsecret_diary_get_entries(entry_date="2026-02-01")
        """
        try:
            logger.info(f"Getting diary entries for {entry_date or 'today'}")

            if entry_date is None:
                entry_date = date.today().strftime("%Y-%m-%d")

            day = diary_api.get_entries(entry_date)

            # Format entries
            entries_list = [
                {
                    "food_entry_id": entry.food_entry_id,
                    "food_id": entry.food_id,
                    "food_name": entry.food_entry_name,
                    "meal": entry.meal,
                    "serving_id": entry.serving_id,
                    "number_of_units": entry.number_of_units,
                    "calories": entry.calories,
                    "carbohydrate": entry.carbohydrate,
                    "protein": entry.protein,
                    "fat": entry.fat,
                }
                for entry in day.entries
            ]

            return {
                "date": day.date,
                "entries": entries_list,
                "total_calories": day.total_calories,
                "total_carbohydrate": day.total_carbohydrate,
                "total_protein": day.total_protein,
                "total_fat": day.total_fat,
            }

        except APIError as e:
            logger.error(f"API error in diary get: {e}")
            return {"error": str(e), "entries": []}
        except Exception as e:
            logger.error(f"Unexpected error in diary get: {e}")
            return {"error": f"Unexpected error: {str(e)}", "entries": []}

    @mcp.tool()
    def fatsecret_diary_get_month(year: Optional[int] = None, month: Optional[int] = None) -> dict:
        """
        Get monthly summary of food diary entries.

        This tool retrieves daily nutritional totals for an entire month,
        useful for tracking trends and progress over time.

        Args:
            year: Year (default: current year)
            month: Month 1-12 (default: current month)

        Returns:
            Dictionary containing:
            - year: Year of data
            - month: Month of data
            - days: List of daily summaries with:
              - date: Date in YYYY-MM-DD format
              - total_calories: Calories for that day
              - total_carbohydrate: Carbs for that day
              - total_protein: Protein for that day
              - total_fat: Fat for that day

        Example:
            Get current month:
            >>> result = fatsecret_diary_get_month()

            Get specific month:
            >>> result = fatsecret_diary_get_month(year=2026, month=1)
            >>> for day in result['days']:
            ...     print(f"{day['date']}: {day['total_calories']} cal")
        """
        try:
            if year is None or month is None:
                today = date.today()
                year = year or today.year
                month = month or today.month

            logger.info(f"Getting diary month: {year}-{month:02d}")

            month_data = diary_api.get_month(year, month)

            # Format days
            days_list = [
                {
                    "date": day.date,
                    "total_calories": day.total_calories,
                    "total_carbohydrate": day.total_carbohydrate,
                    "total_protein": day.total_protein,
                    "total_fat": day.total_fat,
                }
                for day in month_data.days
            ]

            return {"year": month_data.year, "month": month_data.month, "days": days_list}

        except APIError as e:
            logger.error(f"API error in diary get month: {e}")
            return {"error": str(e), "days": []}
        except Exception as e:
            logger.error(f"Unexpected error in diary get month: {e}")
            return {"error": f"Unexpected error: {str(e)}", "days": []}

    @mcp.tool()
    def fatsecret_diary_add_entry(
        food_id: str,
        food_entry_name: str,
        serving_id: str,
        meal: str,
        number_of_units: float = 1.0,
        entry_date: Optional[str] = None,
    ) -> dict:
        """
        Add a food entry to your diary.

        This tool logs a food item to your diary for a specific meal and date.
        Use fatsecret_food_search to find the food_id, then fatsecret_food_get
        to get the serving_id and serving details.

        IMPORTANT: How number_of_units works depends on the serving type:

        For GRAM-BASED servings (description contains "g", e.g. "100 g"):
          - number_of_units is the NUMBER OF GRAMS, not the number of servings!
          - The serving description "100 g" means the unit is 1 gram
          - To log 100g: use number_of_units=100.0
          - To log 150g: use number_of_units=150.0
          - To log 50g: use number_of_units=50.0

        For NON-GRAM servings (e.g. "1 cup", "1 breast", "1 oz"):
          - number_of_units is the number of those servings
          - To log 2 cups: use number_of_units=2.0
          - To log 0.5 breast: use number_of_units=0.5

        RECOMMENDED APPROACH for gram-based requests:
        1. Call fatsecret_food_get to get servings
        2. Find the serving with description containing "g" (e.g. "100 g")
        3. Set number_of_units = desired grams (NOT desired_grams / 100!)

        Args:
            food_id: FatSecret food ID (from fatsecret_food_search)
            food_entry_name: Name of the food entry as it will appear in the diary
                            Example: "Куриная грудка", "Scrambled Eggs"
            serving_id: Serving ID (from fatsecret_food_get servings list).
                       For gram-based logging, pick the serving with "g" in description.
            meal: Meal name - must be one of:
                 "breakfast", "lunch", "dinner", "other"
            number_of_units: For gram servings: number of GRAMS (100g → 100.0).
                            For other servings: number of those servings (2 cups → 2.0).
            entry_date: Date in YYYY-MM-DD format (default: today)

        Returns:
            Dictionary containing:
            - food_entry_id: ID of the created diary entry
            - message: Success message

        Example:
            Add 100g chicken breast to lunch:
            >>> food = fatsecret_food_get(food_id="1641")
            >>> # Find the "100 g" serving (serving_id=50321)
            >>> # For gram serving: number_of_units = desired grams = 100
            >>> result = fatsecret_diary_add_entry(
            ...     food_id="1641",
            ...     food_entry_name="Chicken Breast",
            ...     serving_id="50321",
            ...     meal="lunch",
            ...     number_of_units=100.0  # 100 grams!
            ... )
        """
        try:
            logger.info(f"Adding diary entry: {food_entry_name} ({food_id}) to {meal}")

            # Validate meal
            valid_meals = ["breakfast", "lunch", "dinner", "other"]
            if meal.lower() not in valid_meals:
                return {
                    "error": f"Invalid meal. Must be one of: {', '.join(valid_meals)}",
                }

            entry_id = diary_api.add_entry(
                food_id=food_id,
                serving_id=serving_id,
                meal=meal.lower(),
                number_of_units=number_of_units,
                entry_date=entry_date,
                entry_name=food_entry_name,
            )

            return {
                "food_entry_id": entry_id,
                "message": f"Successfully added entry to {meal}",
            }

        except APIError as e:
            logger.error(f"API error in diary add: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in diary add: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

    @mcp.tool()
    def fatsecret_diary_edit_entry(
        food_entry_id: str,
        serving_id: Optional[str] = None,
        number_of_units: Optional[float] = None,
        meal: Optional[str] = None,
    ) -> dict:
        """
        Edit an existing food diary entry.

        This tool allows you to modify a previously logged food entry.
        You can change the serving size, number of servings, or meal.

        Args:
            food_entry_id: Diary entry ID to edit (from fatsecret_diary_get_entries)
            serving_id: New serving ID (optional)
            number_of_units: New number of servings (optional)
            meal: New meal name (optional) - "breakfast", "lunch", "dinner", "other"

        Returns:
            Dictionary containing:
            - success: True if edit was successful
            - message: Success message

        Example:
            Change serving size:
            >>> result = fatsecret_diary_edit_entry(
            ...     food_entry_id="123456",
            ...     number_of_units=2.5
            ... )

            Move to different meal:
            >>> result = fatsecret_diary_edit_entry(
            ...     food_entry_id="123456",
            ...     meal="lunch"
            ... )
        """
        try:
            logger.info(f"Editing diary entry: {food_entry_id}")

            # Validate meal if provided
            if meal is not None:
                valid_meals = ["breakfast", "lunch", "dinner", "other"]
                if meal.lower() not in valid_meals:
                    return {
                        "error": f"Invalid meal. Must be one of: {', '.join(valid_meals)}",
                    }
                meal = meal.lower()

            diary_api.edit_entry(
                food_entry_id=food_entry_id,
                serving_id=serving_id,
                number_of_units=number_of_units,
                meal=meal,
            )

            return {"success": True, "message": "Diary entry updated successfully"}

        except APIError as e:
            logger.error(f"API error in diary edit: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in diary edit: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

    @mcp.tool()
    def fatsecret_diary_delete_entry(food_entry_id: str) -> dict:
        """
        Delete a food diary entry.

        This tool removes a previously logged food entry from your diary.

        Args:
            food_entry_id: Diary entry ID to delete (from fatsecret_diary_get_entries)

        Returns:
            Dictionary containing:
            - success: True if deletion was successful
            - message: Success message

        Example:
            Delete an entry:
            >>> result = fatsecret_diary_delete_entry(food_entry_id="123456")
        """
        try:
            logger.info(f"Deleting diary entry: {food_entry_id}")

            diary_api.delete_entry(food_entry_id)

            return {"success": True, "message": "Diary entry deleted successfully"}

        except APIError as e:
            logger.error(f"API error in diary delete: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in diary delete: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

    logger.info("Registered food diary tools")
