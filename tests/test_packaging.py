"""The packaging contract: this is what lets `uvx --from git+... fatsecret-mcp` work."""
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _pyproject() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_build_backend_is_a_real_backend():
    """`setuptools.build_backend` does not exist; the name is `setuptools.build_meta`.
    With the typo, every `pip install .` and every uvx launch fails at build time."""
    assert _pyproject()["build-system"]["build-backend"] == "setuptools.build_meta"


def test_console_script_entry_points_exist():
    scripts = _pyproject()["project"]["scripts"]
    assert scripts["fatsecret-mcp"] == "fatsecret_mcp.__main__:main"
    assert scripts["fatsecret-chart"] == "fatsecret_mcp.cli.chart:main"


def test_runtime_dependencies_carry_no_bot_packages():
    """aiogram/openai/claude-agent-sdk belong to the retired bot; pyzbar imports only
    with libzbar0, which python:3.12-slim does not ship. Any of them in the runtime
    deps breaks the container install."""
    deps = " ".join(_pyproject()["project"]["dependencies"]).lower()
    for banned in ("aiogram", "openai", "claude-agent-sdk", "pyzbar", "pillow"):
        assert banned not in deps, f"{banned} must not be a runtime dependency"


def test_package_discovery_is_explicit():
    """Without this, setuptools auto-discovery sees src/, tests/ and nutrition_agent/
    and refuses to guess."""
    assert _pyproject()["tool"]["setuptools"]["packages"]["find"]["where"] == ["src"]


def test_entrypoint_module_imports_without_the_src_prefix():
    """`from src.fatsecret_mcp...` resolves only from the repo root. An installed
    package has no `src` top-level module at all."""
    body = (ROOT / "src" / "fatsecret_mcp" / "__main__.py").read_text(encoding="utf-8")
    assert "from src." not in body and "import src." not in body
