"""Exercise data models."""

from typing import Optional, List
from pydantic import BaseModel, Field


class Exercise(BaseModel):
    """Exercise definition."""

    exercise_id: str
    exercise_name: str
    exercise_description: Optional[str] = None


class ExerciseEntry(BaseModel):
    """Exercise diary entry."""

    exercise_entry_id: str
    exercise_id: str
    exercise_name: str
    minutes: float
    calories: float
    entry_date: str  # Format: YYYY-MM-DD


class ExerciseDay(BaseModel):
    """Exercise entries for a single day."""

    date: str
    entries: List[ExerciseEntry] = Field(default_factory=list)
    total_calories: float = 0.0
    total_minutes: float = 0.0
