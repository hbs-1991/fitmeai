"""MCP tool implementations for the FatSecret API.

Four action-dispatch tools, not twenty thin ones: every tool schema lives in the
model's cached prompt prefix and is paid for on every request.
"""

from .food import register_food_tool
from .diary import register_diary_tool
from .exercise import register_exercise_tool
from .weight import register_weight_tool

__all__ = [
    "register_food_tool",
    "register_diary_tool",
    "register_exercise_tool",
    "register_weight_tool",
]
