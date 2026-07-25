"""The narrow waist, as a test.

Every tool docstring lives in the model's cached prompt prefix and is paid for on
every request, in every session, including cron passes that will never log a meal.
The twenty tools this replaced carried 18,522 characters. Nothing enforces the
saving except this assertion — docstrings grow back one helpful paragraph at a time.
"""
import ast
from pathlib import Path

BUDGET_CHARS = 4800          # ~1.2k tokens
SRC = Path(__file__).resolve().parents[1] / "src" / "fatsecret_mcp" / "tools"
TOOL_FILES = ("food.py", "diary.py", "exercise.py", "weight.py")


def _tool_docstrings():
    for name in TOOL_FILES:
        tree = ast.parse((SRC / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("fatsecret_"):
                yield node.name, ast.get_docstring(node) or ""


def test_exactly_four_tools_are_exposed():
    assert sorted(n for n, _ in _tool_docstrings()) == [
        "fatsecret_diary", "fatsecret_exercise", "fatsecret_food", "fatsecret_weight"]


def test_combined_docstrings_stay_within_the_prefix_budget():
    total = sum(len(d) for _, d in _tool_docstrings())
    assert total <= BUDGET_CHARS, (
        f"tool docstrings total {total} chars, budget is {BUDGET_CHARS}. "
        f"Move procedural detail into a skill instead of the schema.")


def test_every_tool_documents_its_actions():
    for name, doc in _tool_docstrings():
        assert "Actions:" in doc, f"{name} must list its actions"
