"""Recipe data models."""

from typing import Optional, List
from pydantic import BaseModel, Field


class RecipeIngredient(BaseModel):
    """Recipe ingredient."""

    food_id: str
    food_name: str
    serving_id: str
    number_of_units: float
    measurement_description: str
    ingredient_description: str


class Recipe(BaseModel):
    """Recipe information."""

    recipe_id: str
    recipe_name: str
    recipe_description: Optional[str] = None
    recipe_url: Optional[str] = None
    recipe_image: Optional[str] = None
    cooking_time_min: Optional[int] = None
    number_of_servings: Optional[int] = None
    calories_per_serving: Optional[float] = None
    carbohydrate_per_serving: Optional[float] = None
    protein_per_serving: Optional[float] = None
    fat_per_serving: Optional[float] = None
    ingredients: Optional[List[RecipeIngredient]] = Field(default_factory=list)
    directions: Optional[List[str]] = Field(default_factory=list)


class RecipeSearchResult(BaseModel):
    """Recipe search result."""

    recipes: List[Recipe] = Field(default_factory=list)
    total_results: int = 0
    max_results: int = 50
    page_number: int = 0
