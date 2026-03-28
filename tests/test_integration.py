"""
Smoke tests to verify all modules wire together correctly.
These don't require real API keys — they test module loading and wiring.
"""
import pytest
from pathlib import Path


def test_all_modules_import():
    import nutrition_agent
    import nutrition_agent.config
    import nutrition_agent.agent
    import nutrition_agent.bot
    import nutrition_agent.handlers.commands
    import nutrition_agent.handlers.text
    import nutrition_agent.handlers.voice
    import nutrition_agent.handlers.photo
    import nutrition_agent.services.session_manager
    import nutrition_agent.services.barcode
    import nutrition_agent.services.whisper


def test_project_structure():
    root = Path(__file__).parent.parent
    assert (root / "CLAUDE.md").exists(), "CLAUDE.md missing"
    assert (root / "about_me.md").exists(), "about_me.md missing"
    assert (root / "memory" / "MEMORY.md").exists(), "memory/MEMORY.md missing"
    assert (root / ".claude" / "skills").is_dir(), ".claude/skills/ missing"


def test_skills_exist():
    skills_dir = Path(__file__).parent.parent / ".claude" / "skills"
    expected_skills = [
        "quick-log",
        "nutrition-analysis",
        "weight-dynamics",
        "meal-planner",
        "daily-menu",
        "workout-planner",
        "workout-analysis",
        "weekly-report",
    ]
    for skill in expected_skills:
        skill_file = skills_dir / skill / "SKILL.md"
        assert skill_file.exists(), f"Skill {skill}/SKILL.md missing"


def test_agent_creation(tmp_path):
    from nutrition_agent.agent import NutritionAgent

    agent = NutritionAgent(
        project_dir=str(tmp_path),
        mcp_command="python",
        mcp_args=["main.py"],
        mcp_cwd=str(tmp_path),
    )
    opts = agent._build_base_options()
    assert opts.permission_mode == "bypassPermissions"
    assert "fatsecret" in opts.mcp_servers


def test_session_manager_roundtrip(tmp_path):
    from nutrition_agent.services.session_manager import SessionManager

    mgr = SessionManager(str(tmp_path / "sessions.json"))
    mgr.set_session(1, "s1")
    mgr.set_session(1, "s2", thread_id=5)
    assert mgr.get_session(1) == "s1"
    assert mgr.get_session(1, thread_id=5) == "s2"
