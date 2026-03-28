"""Food data models."""

from typing import Optional, List
from pydantic import BaseModel, Field


class ServingInfo(BaseModel):
    """Serving size information."""

    serving_id: Optional[str] = None
    serving_description: str
    serving_url: Optional[str] = None
    metric_serving_amount: Optional[float] = None
    metric_serving_unit: Optional[str] = None
    number_of_units: Optional[float] = None
    measurement_description: Optional[str] = None
    calories: Optional[float] = None
    carbohydrate: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    saturated_fat: Optional[float] = None
    polyunsaturated_fat: Optional[float] = None
    monounsaturated_fat: Optional[float] = None
    trans_fat: Optional[float] = None
    cholesterol: Optional[float] = None
    sodium: Optional[float] = None
    potassium: Optional[float] = None
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    vitamin_a: Optional[float] = None
    vitamin_c: Optional[float] = None
    calcium: Optional[float] = None
    iron: Optional[float] = None


class NutritionInfo(BaseModel):
    """Nutrition information."""

    calories: Optional[float] = None
    carbohydrate: Optional[float] = Field(None, description="Carbohydrates in grams")
    protein: Optional[float] = Field(None, description="Protein in grams")
    fat: Optional[float] = Field(None, description="Total fat in grams")
    saturated_fat: Optional[float] = Field(None, description="Saturated fat in grams")
    polyunsaturated_fat: Optional[float] = None
    monounsaturated_fat: Optional[float] = None
    trans_fat: Optional[float] = None
    cholesterol: Optional[float] = Field(None, description="Cholesterol in mg")
    sodium: Optional[float] = Field(None, description="Sodium in mg")
    potassium: Optional[float] = Field(None, description="Potassium in mg")
    fiber: Optional[float] = Field(None, description="Dietary fiber in grams")
    sugar: Optional[float] = Field(None, description="Sugars in grams")
    vitamin_a: Optional[float] = Field(None, description="Vitamin A as % daily value")
    vitamin_c: Optional[float] = Field(None, description="Vitamin C as % daily value")
    calcium: Optional[float] = Field(None, description="Calcium as % daily value")
    iron: Optional[float] = Field(None, description="Iron as % daily value")


class Food(BaseModel):
    """Food item."""

    food_id: str
    food_name: str
    food_type: Optional[str] = None
    food_url: Optional[str] = None
    food_description: Optional[str] = None
    brand_name: Optional[str] = None
    servings: Optional[List[ServingInfo]] = Field(default_factory=list)


class FoodSearchResult(BaseModel):
    """Food search result."""

    foods: List[Food] = Field(default_factory=list)
    total_results: int = 0
    max_results: int = 50
    page_number: int = 0
