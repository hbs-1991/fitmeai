"""MCP tools for exercise tracking."""

from typing import Optional
from datetime import date
from ..api.base_client import FatSecretClient
from ..api.exercise import ExerciseAPI
from ..utils import get_logger, APIError

logger = get_logger(__name__)


def register_exercise_tools(mcp, client: FatSecretClient):
    """
    Register exercise tracking tools with FastMCP server.

    Args:
        mcp: FastMCP server instance
        client: Authenticated FatSecretClient with user access token
    """
    exercise_api = ExerciseAPI(client)

    @mcp.tool()
    def fatsecret_exercise_search(query: str, max_results: int = 50) -> dict:
        """
        Search for exercises in the FatSecret database.

        This tool searches for exercises by name to find activities you can log.

        Args:
            query: Search query (e.g., "running", "swimming", "yoga")
            max_results: Maximum number of results (default: 50, max: 50)

        Returns:
            Dictionary containing:
            - exercises: List of matching exercises with:
              - exercise_id: Exercise identifier
              - exercise_name: Name of the exercise
              - exercise_description: Description (optional)
            - count: Number of exercises found

        Example:
            Search for running exercises:
            >>> result = fatsecret_exercise_search(query="running")
            >>> for ex in result['exercises']:
            ...     print(f"{ex['exercise_name']} (ID: {ex['exercise_id']})")
        """
        try:
            logger.info(f"Searching exercises: '{query}'")

            if not query or not query.strip():
                return {"error": "Query cannot be empty", "exercises": [], "count": 0}

            max_results = min(max(1, max_results), 50)
            exercises = exercise_api.search(query.strip(), max_results)

            exercises_list = [
                {
                    "exercise_id": ex.exercise_id,
                    "exercise_name": ex.exercise_name,
                    "exercise_description": ex.exercise_description,
                }
                for ex in exercises
            ]

            return {"exercises": exercises_list, "count": len(exercises_list)}

        except APIError as e:
            logger.error(f"API error in exercise search: {e}")
            return {"error": str(e), "exercises": [], "count": 0}
        except Exception as e:
            logger.error(f"Unexpected error in exercise search: {e}")
            return {"error": f"Unexpected error: {str(e)}", "exercises": [], "count": 0}

    @mcp.tool()
    def fatsecret_exercise_get_entries(entry_date: Optional[str] = None) -> dict:
        """
        Get exercise entries for a specific date.

        This tool retrieves all exercises logged for a given date, including
        duration and calories burned.

        Args:
            entry_date: Date in YYYY-MM-DD format (default: today)
                       Example: "2026-02-03"

        Returns:
            Dictionary containing:
            - date: Date of entries
            - entries: List of exercise entries with:
              - exercise_entry_id: Entry identifier
              - exercise_id: Exercise identifier
              - exercise_name: Name of exercise
              - minutes: Duration in minutes
              - calories: Calories burned
            - total_calories: Total calories burned for the day
            - total_minutes: Total exercise time for the day

        Example:
            Get today's exercises:
            >>> result = fatsecret_exercise_get_entries()
            >>> print(f"Total burned: {result['total_calories']} cal")

            Get specific date:
            >>> result = fatsecret_exercise_get_entries(entry_date="2026-02-01")
        """
        try:
            logger.info(f"Getting exercise entries for {entry_date or 'today'}")

            if entry_date is None:
                entry_date = date.today().strftime("%Y-%m-%d")

            day = exercise_api.get_entries(entry_date)

            entries_list = [
                {
                    "exercise_entry_id": entry.exercise_entry_id,
                    "exercise_id": entry.exercise_id,
                    "exercise_name": entry.exercise_name,
                    "minutes": entry.minutes,
                    "calories": entry.calories,
                }
                for entry in day.entries
            ]

            return {
                "date": day.date,
                "entries": entries_list,
                "total_calories": day.total_calories,
                "total_minutes": day.total_minutes,
            }

        except APIError as e:
            logger.error(f"API error in exercise get: {e}")
            return {"error": str(e), "entries": []}
        except Exception as e:
            logger.error(f"Unexpected error in exercise get: {e}")
            return {"error": f"Unexpected error: {str(e)}", "entries": []}

    @mcp.tool()
    def fatsecret_exercise_get_month(
        year: Optional[int] = None, month: Optional[int] = None
    ) -> dict:
        """
        Get monthly summary of exercise entries.

        This tool retrieves daily exercise totals for an entire month.

        Args:
            year: Year (default: current year)
            month: Month 1-12 (default: current month)

        Returns:
            Dictionary containing:
            - year: Year of data
            - month: Month of data
            - days: List of daily summaries with:
              - date: Date in YYYY-MM-DD format
              - total_calories: Calories burned that day
              - total_minutes: Exercise time that day

        Example:
            Get current month:
            >>> result = fatsecret_exercise_get_month()

            Get specific month:
            >>> result = fatsecret_exercise_get_month(year=2026, month=1)
            >>> for day in result['days']:
            ...     print(f"{day['date']}: {day['total_minutes']} min")
        """
        try:
            if year is None or month is None:
                today = date.today()
                year = year or today.year
                month = month or today.month

            logger.info(f"Getting exercise month: {year}-{month:02d}")

            days = exercise_api.get_month(year, month)

            days_list = [
                {
                    "date": day.date,
                    "total_calories": day.total_calories,
                    "total_minutes": day.total_minutes,
                }
                for day in days
            ]

            return {"year": year, "month": month, "days": days_list}

        except APIError as e:
            logger.error(f"API error in exercise get month: {e}")
            return {"error": str(e), "days": []}
        except Exception as e:
            logger.error(f"Unexpected error in exercise get month: {e}")
            return {"error": f"Unexpected error: {str(e)}", "days": []}

    @mcp.tool()
    def fatsecret_exercise_add_entry(
        exercise_id: str, minutes: float, entry_date: Optional[str] = None
    ) -> dict:
        """
        Add an exercise entry to your diary.

        This tool logs exercise activity with duration. Calories burned are
        automatically calculated based on the exercise and your profile.

        Args:
            exercise_id: FatSecret exercise ID (from fatsecret_exercise_search)
            minutes: Duration in minutes (must be positive)
            entry_date: Date in YYYY-MM-DD format (default: today)

        Returns:
            Dictionary containing:
            - exercise_entry_id: ID of the created entry
            - message: Success message

        Example:
            Log 30 minutes of running:
            >>> # First search for the exercise
            >>> search = fatsecret_exercise_search(query="running")
            >>> exercise_id = search['exercises'][0]['exercise_id']
            >>> # Log the exercise
            >>> result = fatsecret_exercise_add_entry(
            ...     exercise_id=exercise_id,
            ...     minutes=30.0
            ... )
        """
        try:
            logger.info(f"Adding exercise entry: {exercise_id} for {minutes} min")

            if minutes <= 0:
                return {"error": "Minutes must be positive"}

            entry_id = exercise_api.add_entry(
                exercise_id=exercise_id, minutes=minutes, entry_date=entry_date
            )

            return {
                "exercise_entry_id": entry_id,
                "message": f"Successfully logged {minutes} minutes of exercise",
            }

        except APIError as e:
            logger.error(f"API error in exercise add: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in exercise add: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

    @mcp.tool()
    def fatsecret_exercise_edit_entry(
        exercise_entry_id: str, minutes: float
    ) -> dict:
        """
        Edit an existing exercise entry.

        This tool allows you to modify the duration of a previously logged exercise.

        Args:
            exercise_entry_id: Exercise entry ID to edit (from fatsecret_exercise_get_entries)
            minutes: New duration in minutes (must be positive)

        Returns:
            Dictionary containing:
            - success: True if edit was successful
            - message: Success message

        Example:
            Change duration to 45 minutes:
            >>> result = fatsecret_exercise_edit_entry(
            ...     exercise_entry_id="123456",
            ...     minutes=45.0
            ... )
        """
        try:
            logger.info(f"Editing exercise entry: {exercise_entry_id}")

            if minutes <= 0:
                return {"error": "Minutes must be positive"}

            exercise_api.edit_entry(exercise_entry_id, minutes)

            return {"success": True, "message": "Exercise entry updated successfully"}

        except APIError as e:
            logger.error(f"API error in exercise edit: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in exercise edit: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

    logger.info("Registered exercise tracking tools")
