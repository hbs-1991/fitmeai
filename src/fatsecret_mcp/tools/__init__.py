"""MCP tool implementations for FatSecret API."""

from .foods_tools import register_food_tools
from .diary_tools import register_diary_tools
from .exercise_tools import register_exercise_tools
from .weight_tools import register_weight_tools

__all__ = [
    "register_food_tools",
    "register_diary_tools",
    "register_exercise_tools",
    "register_weight_tools",
]
