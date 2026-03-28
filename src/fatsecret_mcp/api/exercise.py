"""Exercise API client for FatSecret Platform API."""

from typing import Optional, List
from datetime import date
from ..utils import get_logger
from .base_client import FatSecretClient
from ..models.exercise import Exercise, ExerciseEntry, ExerciseDay

logger = get_logger(__name__)


class ExerciseAPI:
    """Client for FatSecret Exercise API."""

    def __init__(self, client: FatSecretClient):
        """
        Initialize Exercise API client.

        Args:
            client: Authenticated FatSecret client with user access token
        """
        self.client = client

    def search(self, search_expression: str, max_results: int = 50) -> List[Exercise]:
        """
        Search for exercises.

        Args:
            search_expression: Search query (e.g., "running", "swimming")
            max_results: Maximum number of results (default 50)

        Returns:
            List of Exercise objects

        Example:
            >>> api = ExerciseAPI(client)
            >>> exercises = api.search("running")
            >>> for ex in exercises:
            ...     print(ex.exercise_name)
        """
        logger.info(f"Searching exercises: '{search_expression}'")

        response = self.client.post(
            "exercises.search",
            require_auth=False,  # Exercise search is public
            search_expression=search_expression,
            max_results=max_results,
        )

        # Parse response
        exercises = []
        exercises_data = response.get("exercises", {})
        exercise_list = exercises_data.get("exercise", [])

        # Ensure it's a list
        if isinstance(exercise_list, dict):
            exercise_list = [exercise_list]

        for ex_data in exercise_list:
            exercise = Exercise(
                exercise_id=str(ex_data.get("exercise_id", "")),
                exercise_name=ex_data.get("exercise_name", ""),
                exercise_description=ex_data.get("exercise_description"),
            )
            exercises.append(exercise)

        logger.info(f"Found {len(exercises)} exercises")
        return exercises

    def get_entries(self, entry_date: Optional[str] = None) -> ExerciseDay:
        """
        Get exercise entries for a specific date.

        Args:
            entry_date: Date in YYYY-MM-DD format (default: today)

        Returns:
            ExerciseDay object with entries and totals

        Example:
            >>> api = ExerciseAPI(client)
            >>> day = api.get_entries("2026-02-03")
            >>> print(f"Total calories burned: {day.total_calories}")
        """
        if entry_date is None:
            entry_date = date.today().strftime("%Y-%m-%d")

        logger.info(f"Getting exercise entries for {entry_date}")

        response = self.client.post(
            "exercise_entries.get", require_auth=True, date=entry_date
        )

        # Parse response
        entries = []
        total_calories = 0.0
        total_minutes = 0.0

        exercise_entries_data = response.get("exercise_entries", {})
        exercise_entry_list = exercise_entries_data.get("exercise_entry", [])

        # Ensure it's a list
        if isinstance(exercise_entry_list, dict):
            exercise_entry_list = [exercise_entry_list]

        for entry_data in exercise_entry_list:
            entry = ExerciseEntry(
                exercise_entry_id=str(entry_data.get("exercise_entry_id", "")),
                exercise_id=str(entry_data.get("exercise_id", "")),
                exercise_name=entry_data.get("exercise_name", ""),
                minutes=float(entry_data.get("minutes", 0)),
                calories=float(entry_data.get("calories", 0)),
                entry_date=entry_date,
            )
            entries.append(entry)

            total_calories += entry.calories
            total_minutes += entry.minutes

        exercise_day = ExerciseDay(
            date=entry_date,
            entries=entries,
            total_calories=total_calories,
            total_minutes=total_minutes,
        )

        logger.info(f"Retrieved {len(entries)} exercise entries for {entry_date}")
        return exercise_day

    def get_month(
        self, year: Optional[int] = None, month: Optional[int] = None
    ) -> List[ExerciseDay]:
        """
        Get monthly exercise summary.

        Args:
            year: Year (default: current year)
            month: Month 1-12 (default: current month)

        Returns:
            List of ExerciseDay objects with daily summaries

        Example:
            >>> api = ExerciseAPI(client)
            >>> days = api.get_month(2026, 2)
            >>> for day in days:
            ...     print(f"{day.date}: {day.total_calories} cal burned")
        """
        if year is None or month is None:
            today = date.today()
            year = year or today.year
            month = month or today.month

        logger.info(f"Getting exercise month: {year}-{month:02d}")

        response = self.client.post(
            "exercise_entries.get_month", require_auth=True, year=year, month=month
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

                day = ExerciseDay(
                    date=date_str,
                    entries=[],  # Month view doesn't include individual entries
                    total_calories=self._parse_float(day_data.get("calories")) or 0,
                    total_minutes=self._parse_float(day_data.get("minutes")) or 0,
                )
                days.append(day)

        logger.info(f"Retrieved {len(days)} days for {year}-{month:02d}")
        return days

    def add_entry(
        self,
        exercise_id: str,
        minutes: float,
        entry_date: Optional[str] = None,
    ) -> str:
        """
        Add exercise entry to diary.

        Args:
            exercise_id: FatSecret exercise ID
            minutes: Duration in minutes
            entry_date: Date in YYYY-MM-DD format (default: today)

        Returns:
            Exercise entry ID

        Example:
            >>> api = ExerciseAPI(client)
            >>> entry_id = api.add_entry(exercise_id="123", minutes=30.0)
        """
        if entry_date is None:
            entry_date = date.today().strftime("%Y-%m-%d")

        logger.info(f"Adding exercise entry: {exercise_id} for {minutes} min")

        response = self.client.post(
            "exercise_entry.create",
            require_auth=True,
            exercise_id=exercise_id,
            minutes=minutes,
            date=entry_date,
        )

        entry_id = str(response.get("exercise_entry_id", ""))
        logger.info(f"Created exercise entry: {entry_id}")
        return entry_id

    def edit_entry(
        self, exercise_entry_id: str, minutes: Optional[float] = None
    ) -> bool:
        """
        Edit an existing exercise entry.

        Args:
            exercise_entry_id: Exercise entry ID to edit
            minutes: New duration in minutes

        Returns:
            True if successful

        Example:
            >>> api = ExerciseAPI(client)
            >>> api.edit_entry(exercise_entry_id="123", minutes=45.0)
        """
        logger.info(f"Editing exercise entry: {exercise_entry_id}")

        params = {"exercise_entry_id": exercise_entry_id}
        if minutes is not None:
            params["minutes"] = minutes

        self.client.post("exercise_entry.edit", require_auth=True, **params)

        logger.info(f"Edited exercise entry: {exercise_entry_id}")
        return True

    def delete_entry(self, exercise_entry_id: str) -> bool:
        """
        Delete an exercise entry.

        Args:
            exercise_entry_id: Exercise entry ID to delete

        Returns:
            True if successful

        Example:
            >>> api = ExerciseAPI(client)
            >>> api.delete_entry(exercise_entry_id="123")
        """
        logger.info(f"Deleting exercise entry: {exercise_entry_id}")

        self.client.post(
            "exercise_entry.delete", require_auth=True, exercise_entry_id=exercise_entry_id
        )

        logger.info(f"Deleted exercise entry: {exercise_entry_id}")
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
