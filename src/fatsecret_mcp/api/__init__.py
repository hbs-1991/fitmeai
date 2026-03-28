"""API client modules for FatSecret Platform API."""

from .base_client import FatSecretClient
from .foods import FoodsAPI
from .food_diary import FoodDiaryAPI
from .exercise import ExerciseAPI
from .weight import WeightAPI
from .recipes import RecipesAPI

__all__ = [
    "FatSecretClient",
    "FoodsAPI",
    "FoodDiaryAPI",
    "ExerciseAPI",
    "WeightAPI",
    "RecipesAPI",
]
