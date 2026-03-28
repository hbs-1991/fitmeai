"""Food diary data models."""

from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field


class DiaryEntry(BaseModel):
    """Food diary entry."""

    food_entry_id: str
    food_id: str
    food_entry_name: str
    serving_id: str
    number_of_units: float
    meal: str  # "breakfast", "lunch", "dinner", "snack"
    entry_date: str  # Format: YYYY-MM-DD
    calories: Optional[float] = None
    carbohydrate: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None


class DiaryDay(BaseModel):
    """Food diary for a single day."""

    date: str
    entries: List[DiaryEntry] = Field(default_factory=list)
    total_calories: float = 0.0
    total_carbohydrate: float = 0.0
    total_protein: float = 0.0
    total_fat: float = 0.0


class DiaryMonth(BaseModel):
    """Monthly food diary summary."""

    year: int
    month: int
    days: List[DiaryDay] = Field(default_factory=list)
