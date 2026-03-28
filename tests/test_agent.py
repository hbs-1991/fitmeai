import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

from nutrition_agent.agent import NutritionAgent


@pytest.fixture
def agent(tmp_path):
    return NutritionAgent(
        project_dir=str(tmp_path),
        mcp_command="python",
        mcp_args=["main.py"],
        mcp_cwd=str(tmp_path),
    )


def test_agent_builds_base_options(agent):
    opts = agent._build_base_options()
    assert opts.permission_mode == "bypassPermissions"
    assert "Read" in opts.allowed_tools
    assert "Write" in opts.allowed_tools
    assert "Skill" in opts.allowed_tools


def test_agent_builds_resume_options(agent):
    opts = agent._build_resume_options("sess-123")
    assert opts.resume == "sess-123"


def test_agent_mcp_config(agent):
    opts = agent._build_base_options()
    assert "fatsecret" in opts.mcp_servers
    assert opts.mcp_servers["fatsecret"]["command"] == "python"


@pytest.mark.asyncio
async def test_memory_hook_returns_empty_when_no_files(agent):
    result = await agent._load_memory({}, None, None)
    assert result == {}


@pytest.mark.asyncio
async def test_memory_hook_reads_files(agent, tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "MEMORY.md").write_text("# Memory Index\n- patterns", encoding="utf-8")
    (memory_dir / "corrections.md").write_text("chicken = breast", encoding="utf-8")

    result = await agent._load_memory({}, None, None)
    assert "Memory Index" in result["additionalContext"]
    assert "chicken = breast" in result["additionalContext"]
