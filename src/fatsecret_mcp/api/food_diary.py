"""Food Diary API client for FatSecret Platform API."""

from typing import Optional, List
from datetime import date, datetime
from ..utils import get_logger
from .base_client import FatSecretClient
from ..models.diary import DiaryEntry, DiaryDay, DiaryMonth

logger = get_logger(__name__)


class FoodDiaryAPI:
    """Client for FatSecret Food Diary API."""

    MEAL_NAMES = ["breakfast", "lunch", "dinner", "snack", "other"]

    def __init__(self, client: FatSecretClient):
        """
        Initialize Food Diary API client.

        Args:
            client: Authenticated FatSecret client with user access token
        """
        self.client = client

    def get_entries(self, entry_date: Optional[str] = None) -> DiaryDay:
        """
        Get all food diary entries for a specific date.

        Args:
            entry_date: Date in YYYY-MM-DD format (default: today)

        Returns:
            DiaryDay object with all entries and totals

        Example:
            >>> api = FoodDiaryAPI(client)
            >>> day = api.get_entries("2026-02-03")
            >>> print(f"Total calories: {day.total_calories}")
        """
        if entry_date is None:
            entry_date = date.today().strftime("%Y-%m-%d")

        logger.info(f"Getting diary entries for {entry_date}")

        response = self.client.post(
            "food_entries.get", require_auth=True, date=entry_date
        )

        # Parse response
        entries = []
        total_calories = 0.0
        total_carbs = 0.0
        total_protein = 0.0
        total_fat = 0.0

        food_entries_data = response.get("food_entries", {})
        food_entry_list = food_entries_data.get("food_entry", [])

        # Ensure it's a list
        if isinstance(food_entry_list, dict):
            food_entry_list = [food_entry_list]

        for entry_data in food_entry_list:
            entry = DiaryEntry(
                food_entry_id=str(entry_data.get("food_entry_id", "")),
                food_id=str(entry_data.get("food_id", "")),
                food_entry_name=entry_data.get("food_entry_name", ""),
                serving_id=str(entry_data.get("serving_id", "")),
                number_of_units=float(entry_data.get("number_of_units", 0)),
                meal=entry_data.get("meal", "other"),
                entry_date=entry_date,
                calories=self._parse_float(entry_data.get("calories")),
                carbohydrate=self._parse_float(entry_data.get("carbohydrate")),
                protein=self._parse_float(entry_data.get("protein")),
                fat=self._parse_float(entry_data.get("fat")),
            )
            entries.append(entry)

            # Add to totals
            total_calories += entry.calories or 0
            total_carbs += entry.carbohydrate or 0
            total_protein += entry.protein or 0
            total_fat += entry.fat or 0

        diary_day = DiaryDay(
            date=entry_date,
            entries=entries,
            total_calories=total_calories,
            total_carbohydrate=total_carbs,
            total_protein=total_protein,
            total_fat=total_fat,
        )

        logger.info(f"Retrieved {len(entries)} entries for {entry_date}")
        return diary_day

    def get_month(self, year: Optional[int] = None, month: Optional[int] = None) -> DiaryMonth:
        """
        Get monthly summary of food diary.

        Args:
            year: Year (default: current year)
            month: Month 1-12 (default: current month)

        Returns:
            DiaryMonth object with daily summaries

        Example:
            >>> api = FoodDiaryAPI(client)
            >>> month_data = api.get_month(2026, 2)
            >>> for day in month_data.days:
            ...     print(f"{day.date}: {day.total_calories} cal")
        """
        if year is None or month is None:
            today = date.today()
            year = year or today.year
            month = month or today.month

        logger.info(f"Getting diary month: {year}-{month:02d}")

        response = self.client.post(
            "food_entries.get_month", require_auth=True, year=year, month=month
        )

        # Parse response
        days = []
        month_data = response.get("month", {})
        day_list = month_data.get("day", [])

        # Ensure it's a list
        if isinstance(day_list, dict):
            day_list = [day_list]

        for day_data in day_list:
            day_date = day_data.get("date_int")  # Format: YYYYMMDD
            if day_date:
                # Convert YYYYMMDD to YYYY-MM-DD
                date_str = f"{day_date[:4]}-{day_date[4:6]}-{day_date[6:8]}"

                day = DiaryDay(
                    date=date_str,
                    entries=[],  # Month view doesn't include individual entries
                    total_calories=self._parse_float(day_data.get("calories")) or 0,
                    total_carbohydrate=self._parse_float(day_data.get("carbohydrate")) or 0,
                    total_protein=self._parse_float(day_data.get("protein")) or 0,
                    total_fat=self._parse_float(day_data.get("fat")) or 0,
                )
                days.append(day)

        diary_month = DiaryMonth(year=year, month=month, days=days)

        logger.info(f"Retrieved {len(days)} days for {year}-{month:02d}")
        return diary_month

    def add_entry(
        self,
        food_id: str,
        serving_id: str,
        meal: str,
        number_of_units: float = 1.0,
        entry_date: Optional[str] = None,
        entry_name: Optional[str] = None,
    ) -> str:
        """
        Add a food entry to the diary.

        Args:
            food_id: FatSecret food ID
            serving_id: Serving ID from the food
            meal: Meal name (breakfast, lunch, dinner, snack)
            number_of_units: Number of servings (default: 1.0)
            entry_date: Date in YYYY-MM-DD format (default: today)
            entry_name: Custom name for entry (optional)

        Returns:
            Food entry ID

        Example:
            >>> api = FoodDiaryAPI(client)
            >>> entry_id = api.add_entry(
            ...     food_id="12345",
            ...     serving_id="67890",
            ...     meal="breakfast",
            ...     number_of_units=2.0
            ... )
        """
        if entry_date is None:
            entry_date = date.today().strftime("%Y-%m-%d")

        # Validate meal name
        meal = meal.lower()
        if meal not in self.MEAL_NAMES:
            logger.warning(f"Invalid meal name '{meal}', using 'other'")
            meal = "other"

        logger.info(f"Adding diary entry: {food_id} for {meal} on {entry_date}")

        params = {
            "food_id": food_id,
            "serving_id": serving_id,
            "meal": meal,
            "number_of_units": number_of_units,
            "date": entry_date,
        }

        if entry_name:
            params["food_entry_name"] = entry_name

        response = self.client.post("food_entry.create", require_auth=True, **params)

        entry_id = str(response.get("food_entry_id", ""))
        logger.info(f"Created diary entry: {entry_id}")
        return entry_id

    def edit_entry(
        self,
        food_entry_id: str,
        serving_id: Optional[str] = None,
        number_of_units: Optional[float] = None,
        meal: Optional[str] = None,
    ) -> bool:
        """
        Edit an existing diary entry.

        Args:
            food_entry_id: Diary entry ID to edit
            serving_id: New serving ID (optional)
            number_of_units: New number of units (optional)
            meal: New meal name (optional)

        Returns:
            True if successful

        Example:
            >>> api = FoodDiaryAPI(client)
            >>> api.edit_entry(food_entry_id="123", number_of_units=2.5)
        """
        logger.info(f"Editing diary entry: {food_entry_id}")

        params = {"food_entry_id": food_entry_id}

        if serving_id is not None:
            params["serving_id"] = serving_id
        if number_of_units is not None:
            params["number_of_units"] = number_of_units
        if meal is not None:
            meal = meal.lower()
            if meal in self.MEAL_NAMES:
                params["meal"] = meal

        self.client.post("food_entry.edit", require_auth=True, **params)

        logger.info(f"Edited diary entry: {food_entry_id}")
        return True

    def delete_entry(self, food_entry_id: str) -> bool:
        """
        Delete a diary entry.

        Args:
            food_entry_id: Diary entry ID to delete

        Returns:
            True if successful

        Example:
            >>> api = FoodDiaryAPI(client)
            >>> api.delete_entry(food_entry_id="123")
        """
        logger.info(f"Deleting diary entry: {food_entry_id}")

        self.client.post(
            "food_entry.delete", require_auth=True, food_entry_id=food_entry_id
        )

        logger.info(f"Deleted diary entry: {food_entry_id}")
        return True

    @staticmethod
    def _parse_float(value) -> Optional[float]:
        """Parse value to float, return None if invalid."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
