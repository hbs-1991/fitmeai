# Nutrition Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a personal Telegram bot powered by Claude Agent SDK that uses FatSecret MCP tools for nutrition tracking, meal planning, exercise logging, and weekly analysis.

**Architecture:** aiogram 3.26 Telegram bot receives messages (text/voice/photo) → preprocesses (Whisper for voice, pyzbar for barcodes, base64 for images) → passes to Claude Agent SDK with FatSecret MCP server → streams response back via sendMessageDraft. Session persistence maps Telegram chat_id to Agent SDK session_id. Memory system uses hooks to load and Write tool to update.

**Tech Stack:** Python 3.10+, claude-agent-sdk 0.1.51+, aiogram 3.26+, openai (Whisper), pyzbar, Pillow

**Spec:** `docs/superpowers/specs/2026-03-28-nutrition-agent-design.md`

---

## File Map

| File | Responsibility | Task |
|------|---------------|------|
| `pyproject.toml` | Add new dependencies | 1 |
| `.env.example` | Environment variable template | 1 |
| `.gitignore` | Add memory/ exclusions | 1 |
| `nutrition_agent/__init__.py` | Package init | 2 |
| `nutrition_agent/config.py` | Load env vars, constants | 2 |
| `nutrition_agent/services/session_manager.py` | chat_id ↔ session_id persistence | 3 |
| `nutrition_agent/services/barcode.py` | pyzbar barcode decoding | 4 |
| `nutrition_agent/services/whisper.py` | OpenAI Whisper transcription | 5 |
| `nutrition_agent/agent.py` | Agent SDK wrapper: query, resume, hooks, streaming | 6 |
| `nutrition_agent/handlers/commands.py` | /start, /help, /profile, /newsession | 7 |
| `nutrition_agent/handlers/text.py` | Text message → agent | 8 |
| `nutrition_agent/handlers/voice.py` | Voice → Whisper → agent | 8 |
| `nutrition_agent/handlers/photo.py` | Photo → barcode or image → agent | 9 |
| `nutrition_agent/handlers/__init__.py` | Register all handlers | 10 |
| `nutrition_agent/bot.py` | aiogram Bot + Dispatcher setup | 10 |
| `run_bot.py` | Entry point | 10 |
| `CLAUDE.md` | Agent system instructions | 11 |
| `about_me.md` | User profile template | 11 |
| `memory/MEMORY.md` | Memory index (initial) | 11 |
| `memory/eating_patterns.md` | Initial empty file | 11 |
| `memory/favorite_foods.md` | Initial empty file | 11 |
| `memory/corrections.md` | Initial empty file | 11 |
| `memory/weekly_insights.md` | Initial empty file | 11 |
| `.claude/skills/quick-log/SKILL.md` | Quick food logging skill | 12 |
| `.claude/skills/nutrition-analysis/SKILL.md` | Nutrition analysis skill | 12 |
| `.claude/skills/weight-dynamics/SKILL.md` | Weight tracking skill | 12 |
| `.claude/skills/meal-planner/SKILL.md` | Meal planning skill | 12 |
| `.claude/skills/daily-menu/SKILL.md` | Daily menu skill | 12 |
| `.claude/skills/workout-planner/SKILL.md` | Workout planning skill | 12 |
| `.claude/skills/workout-analysis/SKILL.md` | Workout analysis skill | 12 |
| `.claude/skills/weekly-report/SKILL.md` | Weekly report skill | 12 |
| `tests/test_config.py` | Config loading tests | 2 |
| `tests/test_session_manager.py` | Session manager tests | 3 |
| `tests/test_barcode.py` | Barcode service tests | 4 |
| `tests/test_whisper.py` | Whisper service tests | 5 |
| `tests/test_agent.py` | Agent wrapper tests | 6 |

---

### Task 1: Project Setup — Dependencies and Environment

**Files:**
- Modify: `pyproject.toml`
- Modify: `.gitignore`
- Create: `.env.example`

- [ ] **Step 1: Add new dependencies to pyproject.toml**

```toml
# In pyproject.toml, replace the [project] dependencies list with:
dependencies = [
    "fastmcp>=3.0.0b1",
    "requests>=2.31.0",
    "pydantic>=2.5.0",
    "python-dotenv>=1.0.0",
    "keyring>=24.0.0",
    "claude-agent-sdk>=0.1.51",
    "aiogram>=3.26.0",
    "openai>=1.0.0",
    "pyzbar>=0.1.9",
    "Pillow>=10.0.0",
]
```

- [ ] **Step 2: Update .gitignore**

Append to `.gitignore`:

```
# Nutrition agent
sessions.json
tmp/
```

- [ ] **Step 3: Create .env.example**

```env
# Anthropic — choose ONE:
# Option A: OAuth token from subscription (preferred, $0 cost)
# Run: claude setup-token
ANTHROPIC_AUTH_TOKEN=

# Option B: API key (paid per token)
# ANTHROPIC_API_KEY=sk-ant-...

# Telegram Bot (from @BotFather)
TELEGRAM_BOT_TOKEN=

# OpenAI (Whisper voice transcription only)
OPENAI_API_KEY=

# FatSecret (existing)
FATSECRET_CLIENT_ID=
FATSECRET_CLIENT_SECRET=
```

- [ ] **Step 4: Install dependencies**

Run: `pip install -e ".[dev]"`
Expected: All packages install successfully, including claude-agent-sdk, aiogram, openai, pyzbar, Pillow.

- [ ] **Step 5: Verify installations**

Run: `python -c "import claude_agent_sdk; import aiogram; import openai; import pyzbar; print('All imports OK')"`
Expected: `All imports OK`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .gitignore .env.example
git commit -m "feat: add nutrition agent dependencies and env template"
```

---

### Task 2: Config Module

**Files:**
- Create: `nutrition_agent/__init__.py`
- Create: `nutrition_agent/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Create package init**

```python
# nutrition_agent/__init__.py
```

(Empty file — just makes it a package.)

- [ ] **Step 2: Write failing test for config**

```python
# tests/test_config.py
import os
import pytest


def test_config_loads_telegram_token(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token-123")
    monkeypatch.setenv("FATSECRET_CLIENT_ID", "cid")
    monkeypatch.setenv("FATSECRET_CLIENT_SECRET", "csec")

    from nutrition_agent.config import Config

    cfg = Config()
    assert cfg.telegram_bot_token == "test-token-123"


def test_config_raises_without_telegram_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

    from nutrition_agent.config import Config

    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
        Config()


def test_config_optional_openai_key(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("FATSECRET_CLIENT_ID", "cid")
    monkeypatch.setenv("FATSECRET_CLIENT_SECRET", "csec")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from nutrition_agent.config import Config

    cfg = Config()
    assert cfg.openai_api_key is None


def test_config_project_dir():
    from nutrition_agent.config import PROJECT_DIR

    assert PROJECT_DIR.exists()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'nutrition_agent.config'`

- [ ] **Step 4: Implement config**

```python
# nutrition_agent/config.py
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parent.parent


class Config:
    def __init__(self) -> None:
        self.telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        self.openai_api_key: str | None = os.environ.get("OPENAI_API_KEY")
        self.anthropic_auth_token: str | None = os.environ.get("ANTHROPIC_AUTH_TOKEN")
        self.anthropic_api_key: str | None = os.environ.get("ANTHROPIC_API_KEY")

        self.fatsecret_client_id = os.environ.get("FATSECRET_CLIENT_ID", "")
        self.fatsecret_client_secret = os.environ.get("FATSECRET_CLIENT_SECRET", "")
        if not self.fatsecret_client_id or not self.fatsecret_client_secret:
            raise ValueError(
                "FATSECRET_CLIENT_ID and FATSECRET_CLIENT_SECRET are required"
            )

        self.mcp_server_command = "python"
        self.mcp_server_args = ["main.py"]
        self.mcp_server_cwd = str(PROJECT_DIR)
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_config.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add nutrition_agent/__init__.py nutrition_agent/config.py tests/test_config.py
git commit -m "feat: add nutrition agent config module"
```

---

### Task 3: Session Manager Service

**Files:**
- Create: `nutrition_agent/services/__init__.py`
- Create: `nutrition_agent/services/session_manager.py`
- Create: `tests/test_session_manager.py`

- [ ] **Step 1: Create services package init**

```python
# nutrition_agent/services/__init__.py
```

- [ ] **Step 2: Write failing tests**

```python
# tests/test_session_manager.py
import json
import pytest
from pathlib import Path

from nutrition_agent.services.session_manager import SessionManager


@pytest.fixture
def storage_path(tmp_path):
    return str(tmp_path / "sessions.json")


def test_set_and_get_session(storage_path):
    mgr = SessionManager(storage_path)
    mgr.set_session(chat_id=123, session_id="sess-abc")
    assert mgr.get_session(chat_id=123) == "sess-abc"


def test_get_nonexistent_session(storage_path):
    mgr = SessionManager(storage_path)
    assert mgr.get_session(chat_id=999) is None


def test_thread_id_isolation(storage_path):
    mgr = SessionManager(storage_path)
    mgr.set_session(chat_id=123, session_id="sess-main", thread_id=None)
    mgr.set_session(chat_id=123, session_id="sess-diary", thread_id=42)

    assert mgr.get_session(chat_id=123) == "sess-main"
    assert mgr.get_session(chat_id=123, thread_id=42) == "sess-diary"


def test_persistence_across_instances(storage_path):
    mgr1 = SessionManager(storage_path)
    mgr1.set_session(chat_id=10, session_id="sess-persist")

    mgr2 = SessionManager(storage_path)
    assert mgr2.get_session(chat_id=10) == "sess-persist"


def test_clear_session(storage_path):
    mgr = SessionManager(storage_path)
    mgr.set_session(chat_id=123, session_id="sess-old")
    mgr.clear_session(chat_id=123)
    assert mgr.get_session(chat_id=123) is None
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_session_manager.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement SessionManager**

```python
# nutrition_agent/services/session_manager.py
from __future__ import annotations

import json
from pathlib import Path


class SessionManager:
    def __init__(self, storage_path: str) -> None:
        self._path = Path(storage_path)
        self._sessions: dict[str, str] = {}
        self._load()

    def _key(self, chat_id: int, thread_id: int | None = None) -> str:
        return f"{chat_id}:{thread_id or 0}"

    def get_session(self, chat_id: int, thread_id: int | None = None) -> str | None:
        return self._sessions.get(self._key(chat_id, thread_id))

    def set_session(
        self, chat_id: int, session_id: str, thread_id: int | None = None
    ) -> None:
        self._sessions[self._key(chat_id, thread_id)] = session_id
        self._save()

    def clear_session(self, chat_id: int, thread_id: int | None = None) -> None:
        key = self._key(chat_id, thread_id)
        self._sessions.pop(key, None)
        self._save()

    def _load(self) -> None:
        if self._path.exists():
            self._sessions = json.loads(self._path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._sessions, indent=2), encoding="utf-8"
        )
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_session_manager.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add nutrition_agent/services/__init__.py nutrition_agent/services/session_manager.py tests/test_session_manager.py
git commit -m "feat: add session manager for chat_id to session_id mapping"
```

---

### Task 4: Barcode Service

**Files:**
- Create: `nutrition_agent/services/barcode.py`
- Create: `tests/test_barcode.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_barcode.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from nutrition_agent.services.barcode import decode_barcode


def test_decode_barcode_returns_none_for_no_barcode(tmp_path):
    # Create a simple blank image (no barcode)
    from PIL import Image

    img = Image.new("RGB", (100, 100), color="white")
    img_path = tmp_path / "blank.jpg"
    img.save(str(img_path))

    result = decode_barcode(str(img_path))
    assert result is None


def test_decode_barcode_returns_string_when_found():
    mock_barcode = MagicMock()
    mock_barcode.data = b"4600682500117"
    mock_barcode.type = "EAN13"

    with patch("nutrition_agent.services.barcode.pyzbar_decode", return_value=[mock_barcode]):
        result = decode_barcode("dummy_path.jpg")
        assert result == "4600682500117"


def test_decode_barcode_returns_none_on_error():
    with patch("nutrition_agent.services.barcode.pyzbar_decode", side_effect=Exception("bad")):
        result = decode_barcode("nonexistent.jpg")
        assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_barcode.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement barcode service**

```python
# nutrition_agent/services/barcode.py
from __future__ import annotations

import logging

from PIL import Image
from pyzbar.pyzbar import decode as pyzbar_decode

logger = logging.getLogger(__name__)


def decode_barcode(image_path: str) -> str | None:
    """Try to decode a barcode from an image. Returns barcode string or None."""
    try:
        image = Image.open(image_path)
        barcodes = pyzbar_decode(image)
        if barcodes:
            return barcodes[0].data.decode("utf-8")
        return None
    except Exception:
        logger.exception("Failed to decode barcode from %s", image_path)
        return None
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_barcode.py -v`
Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add nutrition_agent/services/barcode.py tests/test_barcode.py
git commit -m "feat: add barcode decoding service using pyzbar"
```

---

### Task 5: Whisper Transcription Service

**Files:**
- Create: `nutrition_agent/services/whisper.py`
- Create: `tests/test_whisper.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_whisper.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from nutrition_agent.services.whisper import transcribe_voice


@pytest.mark.asyncio
async def test_transcribe_voice_returns_text():
    mock_response = MagicMock()
    mock_response.text = "Я съел овсянку на завтрак"

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = MagicMock(return_value=mock_response)

    with patch("nutrition_agent.services.whisper._get_client", return_value=mock_client):
        result = await transcribe_voice("/tmp/voice.ogg")
        assert result == "Я съел овсянку на завтрак"


@pytest.mark.asyncio
async def test_transcribe_voice_returns_none_without_api_key():
    with patch("nutrition_agent.services.whisper._get_client", return_value=None):
        result = await transcribe_voice("/tmp/voice.ogg")
        assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_whisper.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement whisper service**

```python
# nutrition_agent/services/whisper.py
from __future__ import annotations

import logging
import os

from openai import OpenAI

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI | None:
    global _client
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    if _client is None:
        _client = OpenAI(api_key=api_key)
    return _client


async def transcribe_voice(file_path: str) -> str | None:
    """Transcribe an audio file using OpenAI Whisper API. Returns text or None."""
    client = _get_client()
    if client is None:
        logger.warning("OPENAI_API_KEY not set, cannot transcribe voice")
        return None

    try:
        with open(file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ru",
            )
        return response.text
    except Exception:
        logger.exception("Failed to transcribe %s", file_path)
        return None
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_whisper.py -v`
Expected: All 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add nutrition_agent/services/whisper.py tests/test_whisper.py
git commit -m "feat: add Whisper voice transcription service"
```

---

### Task 6: Agent SDK Wrapper

**Files:**
- Create: `nutrition_agent/agent.py`
- Create: `tests/test_agent.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_agent.py
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


def test_memory_hook_returns_empty_when_no_files(agent):
    import asyncio
    result = asyncio.get_event_loop().run_until_complete(
        agent._load_memory({}, None, None)
    )
    assert result == {}


def test_memory_hook_reads_files(agent, tmp_path):
    import asyncio

    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "MEMORY.md").write_text("# Memory Index\n- patterns", encoding="utf-8")
    (memory_dir / "corrections.md").write_text("chicken = breast", encoding="utf-8")

    result = asyncio.get_event_loop().run_until_complete(
        agent._load_memory({}, None, None)
    )
    assert "Memory Index" in result["additionalContext"]
    assert "chicken = breast" in result["additionalContext"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_agent.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement agent wrapper**

```python
# nutrition_agent/agent.py
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, AsyncIterator

from claude_agent_sdk import (
    ClaudeAgentOptions,
    HookMatcher,
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    query,
)

logger = logging.getLogger(__name__)


class NutritionAgent:
    def __init__(
        self,
        project_dir: str,
        mcp_command: str,
        mcp_args: list[str],
        mcp_cwd: str,
    ) -> None:
        self._project_dir = Path(project_dir)
        self._mcp_command = mcp_command
        self._mcp_args = mcp_args
        self._mcp_cwd = mcp_cwd

    def _build_base_options(self) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            system_prompt={
                "type": "preset",
                "preset": "claude_code",
            },
            setting_sources=["project"],
            cwd=str(self._project_dir),
            permission_mode="bypassPermissions",
            mcp_servers={
                "fatsecret": {
                    "command": self._mcp_command,
                    "args": self._mcp_args,
                    "cwd": self._mcp_cwd,
                }
            },
            allowed_tools=[
                "Read",
                "Write",
                "Skill",
                "mcp__fatsecret__*",
            ],
            max_turns=20,
            hooks={
                "UserPromptSubmit": [
                    HookMatcher(matcher=".*", hooks=[self._load_memory])
                ]
            },
        )

    def _build_resume_options(self, session_id: str) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(resume=session_id)

    async def _load_memory(
        self,
        input_data: dict[str, Any],
        tool_use_id: str | None,
        context: Any,
    ) -> dict[str, Any]:
        memory_dir = self._project_dir / "memory"
        if not memory_dir.exists():
            return {}

        parts: list[str] = []

        index = memory_dir / "MEMORY.md"
        if index.exists():
            parts.append(index.read_text(encoding="utf-8"))

        for f in sorted(memory_dir.glob("*.md")):
            if f.name != "MEMORY.md":
                parts.append(f"## {f.stem}\n{f.read_text(encoding='utf-8')}")

        if not parts:
            return {}

        return {"additionalContext": "\n\n".join(parts)}

    async def send_text(
        self, prompt: str, session_id: str | None = None
    ) -> AsyncIterator[tuple[str, str | None, str | None]]:
        """Send text prompt to agent. Yields (text_chunk, session_id, result)."""
        if session_id:
            options = self._build_resume_options(session_id)
        else:
            options = self._build_base_options()

        new_session_id: str | None = None
        result_text: str | None = None

        async for message in query(prompt=prompt, options=options):
            if isinstance(message, SystemMessage):
                if hasattr(message, "subtype") and message.subtype == "init":
                    new_session_id = getattr(message, "session_id", None)
                    yield ("", new_session_id, None)

            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield (block.text, new_session_id, None)

            elif isinstance(message, ResultMessage):
                result_text = getattr(message, "result", None)
                yield ("", new_session_id, result_text)

    async def send_image(
        self, image_path: str, text: str, session_id: str | None = None
    ) -> AsyncIterator[tuple[str, str | None, str | None]]:
        """Send image + text to agent via streaming input."""
        import base64

        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

        media_type = "image/jpeg"
        if image_path.lower().endswith(".png"):
            media_type = "image/png"

        async def message_stream():
            yield {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_b64,
                            },
                        },
                    ],
                },
            }

        if session_id:
            options = self._build_resume_options(session_id)
        else:
            options = self._build_base_options()

        new_session_id: str | None = None

        async for message in query(prompt=message_stream(), options=options):
            if isinstance(message, SystemMessage):
                if hasattr(message, "subtype") and message.subtype == "init":
                    new_session_id = getattr(message, "session_id", None)
                    yield ("", new_session_id, None)

            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield (block.text, new_session_id, None)

            elif isinstance(message, ResultMessage):
                result_text = getattr(message, "result", None)
                yield ("", new_session_id, result_text)
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_agent.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add nutrition_agent/agent.py tests/test_agent.py
git commit -m "feat: add Agent SDK wrapper with MCP, memory hooks, and image streaming"
```

---

### Task 7: Telegram Command Handlers

**Files:**
- Create: `nutrition_agent/handlers/__init__.py`
- Create: `nutrition_agent/handlers/commands.py`

- [ ] **Step 1: Create handlers package init**

```python
# nutrition_agent/handlers/__init__.py
```

- [ ] **Step 2: Implement command handlers**

```python
# nutrition_agent/handlers/commands.py
from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! Я твой персональный нутрициолог и фитнес-тренер.\n\n"
        "Что я умею:\n"
        "- Отправь фото еды — я распознаю и добавлю в дневник\n"
        "- Отправь фото баркода — найду продукт\n"
        "- Отправь голосовое — пойму и обработаю\n"
        "- Напиши что съел — добавлю в дневник\n\n"
        "Команды:\n"
        "/help — справка\n"
        "/profile — показать профиль\n"
        "/newsession — начать новый диалог\n"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Просто напиши мне:\n"
        "- «Я съел 200г куриной грудки» — запишу в дневник\n"
        "- «Проанализируй мое питание за неделю» — анализ\n"
        "- «Составь план питания» — план на неделю\n"
        "- «Что мне есть сегодня?» — меню на день\n"
        "- «Динамика веса» — прогресс по весу\n"
        "- «Отчет за неделю» — полный отчет\n"
    )


@router.message(Command("newsession"))
async def cmd_new_session(message: Message) -> None:
    # Session clearing is handled by the bot.py middleware
    # We just signal via message.text that a new session is needed
    await message.answer("Начинаю новый диалог. Предыдущий контекст сброшен.")
```

- [ ] **Step 3: Commit**

```bash
git add nutrition_agent/handlers/__init__.py nutrition_agent/handlers/commands.py
git commit -m "feat: add Telegram command handlers (/start, /help, /newsession)"
```

---

### Task 8: Text and Voice Handlers

**Files:**
- Create: `nutrition_agent/handlers/text.py`
- Create: `nutrition_agent/handlers/voice.py`

- [ ] **Step 1: Implement text handler**

```python
# nutrition_agent/handlers/text.py
from __future__ import annotations

import logging

from aiogram import Bot, Router
from aiogram.types import Message

from nutrition_agent.agent import NutritionAgent
from nutrition_agent.services.session_manager import SessionManager

logger = logging.getLogger(__name__)

router = Router()

# These are injected by bot.py at setup time
_agent: NutritionAgent | None = None
_sessions: SessionManager | None = None


def setup(agent: NutritionAgent, sessions: SessionManager) -> None:
    global _agent, _sessions
    _agent = agent
    _sessions = sessions


@router.message()
async def handle_text(message: Message) -> None:
    if not message.text or not _agent or not _sessions:
        return

    chat_id = message.chat.id
    thread_id = message.message_thread_id
    session_id = _sessions.get_session(chat_id, thread_id)

    bot: Bot = message.bot  # type: ignore[assignment]
    draft_id = message.message_id
    accumulated = ""

    await bot.send_chat_action(chat_id=chat_id, action="typing")

    async for text_chunk, new_session_id, result in _agent.send_text(
        prompt=message.text, session_id=session_id
    ):
        if new_session_id and not session_id:
            session_id = new_session_id
            _sessions.set_session(chat_id, new_session_id, thread_id)

        if text_chunk:
            accumulated += text_chunk
            try:
                await bot.send_message_draft(
                    chat_id=chat_id,
                    draft_id=draft_id,
                    text=accumulated[:4096],
                )
            except Exception:
                pass  # draft streaming is best-effort

    if accumulated:
        await message.answer(accumulated[:4096])
    elif not accumulated:
        await message.answer("Не удалось получить ответ. Попробуй ещё раз.")
```

- [ ] **Step 2: Implement voice handler**

```python
# nutrition_agent/handlers/voice.py
from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from aiogram import Bot, Router
from aiogram.types import Message

from nutrition_agent.agent import NutritionAgent
from nutrition_agent.services.session_manager import SessionManager
from nutrition_agent.services.whisper import transcribe_voice

logger = logging.getLogger(__name__)

router = Router()

_agent: NutritionAgent | None = None
_sessions: SessionManager | None = None


def setup(agent: NutritionAgent, sessions: SessionManager) -> None:
    global _agent, _sessions
    _agent = agent
    _sessions = sessions


@router.message(lambda m: m.voice is not None)
async def handle_voice(message: Message) -> None:
    if not _agent or not _sessions:
        return

    bot: Bot = message.bot  # type: ignore[assignment]
    chat_id = message.chat.id
    thread_id = message.message_thread_id

    await bot.send_chat_action(chat_id=chat_id, action="typing")

    # Download voice file
    voice = message.voice
    file = await bot.get_file(voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        await bot.download_file(file.file_path, tmp.name)
        tmp_path = tmp.name

    try:
        text = await transcribe_voice(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if not text:
        await message.answer("Не удалось распознать голосовое сообщение.")
        return

    await message.answer(f"Распознано: {text}")

    # Process transcribed text through agent
    session_id = _sessions.get_session(chat_id, thread_id)
    accumulated = ""
    draft_id = message.message_id

    async for text_chunk, new_session_id, result in _agent.send_text(
        prompt=f"[Голосовое сообщение]: {text}", session_id=session_id
    ):
        if new_session_id and not session_id:
            session_id = new_session_id
            _sessions.set_session(chat_id, new_session_id, thread_id)

        if text_chunk:
            accumulated += text_chunk
            try:
                await bot.send_message_draft(
                    chat_id=chat_id, draft_id=draft_id, text=accumulated[:4096]
                )
            except Exception:
                pass

    if accumulated:
        await message.answer(accumulated[:4096])
```

- [ ] **Step 3: Commit**

```bash
git add nutrition_agent/handlers/text.py nutrition_agent/handlers/voice.py
git commit -m "feat: add text and voice message handlers with streaming response"
```

---

### Task 9: Photo Handler (Barcode + Food Images)

**Files:**
- Create: `nutrition_agent/handlers/photo.py`

- [ ] **Step 1: Implement photo handler**

```python
# nutrition_agent/handlers/photo.py
from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from aiogram import Bot, Router
from aiogram.types import Message

from nutrition_agent.agent import NutritionAgent
from nutrition_agent.services.barcode import decode_barcode
from nutrition_agent.services.session_manager import SessionManager

logger = logging.getLogger(__name__)

router = Router()

_agent: NutritionAgent | None = None
_sessions: SessionManager | None = None


def setup(agent: NutritionAgent, sessions: SessionManager) -> None:
    global _agent, _sessions
    _agent = agent
    _sessions = sessions


@router.message(lambda m: m.photo is not None)
async def handle_photo(message: Message) -> None:
    if not _agent or not _sessions:
        return

    bot: Bot = message.bot  # type: ignore[assignment]
    chat_id = message.chat.id
    thread_id = message.message_thread_id

    await bot.send_chat_action(chat_id=chat_id, action="typing")

    # Download the largest photo
    photo = message.photo[-1]  # Largest size
    file = await bot.get_file(photo.file_id)

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        await bot.download_file(file.file_path, tmp.name)
        tmp_path = tmp.name

    session_id = _sessions.get_session(chat_id, thread_id)
    caption = message.caption or ""

    try:
        # Try barcode first
        barcode = decode_barcode(tmp_path)

        if barcode:
            await message.answer(f"Баркод: {barcode}. Ищу продукт...")
            prompt = f"Найди продукт по баркоду {barcode} и покажи информацию о питательной ценности"
            send = _agent.send_text(prompt=prompt, session_id=session_id)
        else:
            # No barcode — treat as food photo
            text = caption or "Определи что за еда на фото, оцени порцию и предложи записать в дневник"
            send = _agent.send_image(
                image_path=tmp_path, text=text, session_id=session_id
            )

        accumulated = ""
        draft_id = message.message_id

        async for text_chunk, new_session_id, result in send:
            if new_session_id and not session_id:
                session_id = new_session_id
                _sessions.set_session(chat_id, new_session_id, thread_id)

            if text_chunk:
                accumulated += text_chunk
                try:
                    await bot.send_message_draft(
                        chat_id=chat_id, draft_id=draft_id, text=accumulated[:4096]
                    )
                except Exception:
                    pass

        if accumulated:
            await message.answer(accumulated[:4096])

    finally:
        Path(tmp_path).unlink(missing_ok=True)
```

- [ ] **Step 2: Commit**

```bash
git add nutrition_agent/handlers/photo.py
git commit -m "feat: add photo handler with barcode detection and food image analysis"
```

---

### Task 10: Bot Assembly and Entry Point

**Files:**
- Create: `nutrition_agent/bot.py`
- Create: `run_bot.py`

- [ ] **Step 1: Implement bot.py**

```python
# nutrition_agent/bot.py
from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from nutrition_agent.agent import NutritionAgent
from nutrition_agent.config import Config, PROJECT_DIR
from nutrition_agent.handlers import commands, text, voice, photo
from nutrition_agent.services.session_manager import SessionManager

logger = logging.getLogger(__name__)


def create_bot(config: Config) -> tuple[Bot, Dispatcher]:
    bot = Bot(
        token=config.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher()

    # Services
    sessions = SessionManager(str(PROJECT_DIR / "sessions.json"))

    agent = NutritionAgent(
        project_dir=str(PROJECT_DIR),
        mcp_command=config.mcp_server_command,
        mcp_args=config.mcp_server_args,
        mcp_cwd=config.mcp_server_cwd,
    )

    # Inject dependencies into handlers
    text.setup(agent, sessions)
    voice.setup(agent, sessions)
    photo.setup(agent, sessions)

    # Register routers (order matters: commands first, then specific types, then text fallback)
    dp.include_router(commands.router)
    dp.include_router(voice.router)
    dp.include_router(photo.router)
    dp.include_router(text.router)

    return bot, dp
```

- [ ] **Step 2: Implement run_bot.py entry point**

```python
# run_bot.py
import asyncio
import logging

from nutrition_agent.bot import create_bot
from nutrition_agent.config import Config


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = Config()
    bot, dp = create_bot(config)

    logging.info("Starting Nutrition Agent bot...")
    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Test that bot assembles without errors**

Run: `python -c "from nutrition_agent.bot import create_bot; print('Bot module OK')"`
Expected: `Bot module OK` (requires .env with TELEGRAM_BOT_TOKEN set)

- [ ] **Step 4: Commit**

```bash
git add nutrition_agent/bot.py run_bot.py
git commit -m "feat: add bot assembly and entry point"
```

---

### Task 11: CLAUDE.md, User Profile, and Memory Files

**Files:**
- Create: `CLAUDE.md`
- Create: `about_me.md`
- Create: `memory/MEMORY.md`
- Create: `memory/eating_patterns.md`
- Create: `memory/favorite_foods.md`
- Create: `memory/corrections.md`
- Create: `memory/weekly_insights.md`

- [ ] **Step 1: Create CLAUDE.md**

```markdown
# Nutrition Agent

Ты — персональный нутрициолог и фитнес-тренер. Ты помогаешь пользователю
отслеживать питание, планировать приёмы пищи, анализировать паттерны питания,
предлагать тренировки и поддерживать здоровый образ жизни.

## Профиль пользователя
Прочитай @about_me.md — там все данные о пользователе: параметры, цели,
предпочтения. Всегда учитывай их при рекомендациях.

## Память
Твои файлы памяти в папке memory/. Они загружаются автоматически при старте сессии.
Когда узнаёшь что-то новое о привычках пользователя:
- Новый частый продукт → Write в memory/favorite_foods.md
- Коррекция пользователя → Write в memory/corrections.md
- Новый паттерн питания → Write в memory/eating_patterns.md
- Вывод из анализа → Write в memory/weekly_insights.md
- Обнови memory/MEMORY.md индекс после изменений

## Стиль общения
- Отвечай на русском языке
- Будь кратким, но информативным
- Используй таблицы для данных о питании
- Всегда показывай КБЖУ (калории, белки, жиры, углеводы)
- Предупреждай если дневной калораж отклоняется >20% от цели

## Доступные инструменты
- FatSecret MCP tools — поиск еды, дневник, упражнения, вес
- Read — просмотр фото еды
- Write — обновление файлов памяти
- Skills — анализ и планирование

## Правила работы
- Фото еды: определи блюдо, оцени порцию, найди в FatSecret, подтверди перед добавлением
- Фото баркода: найди по номеру баркода
- Запрос анализа: используй соответствующий Skill
- Запрос плана: используй Skill планирования
- Всегда подтверждай перед добавлением/редактированием/удалением записей дневника
```

- [ ] **Step 2: Create about_me.md template**

```markdown
# Профиль пользователя

## Физические параметры
- Пол: мужской
- Возраст: ___ лет
- Рост: ___ см
- Текущий вес: ___ кг
- Целевой вес: ___ кг

## Цели
- Основная цель: похудение / набор массы / поддержание
- Целевой калораж: ___ ккал/день
- БЖУ цель: белки ___г / жиры ___г / углеводы ___г

## Образ жизни
- Уровень активности: сидячая работа / умеренная / активная
- Тренировки: ___ раз в неделю, тип: ___
- Рабочий график: с ___:___ до ___:___
- Сон: с ___:___ до ___:___

## Пищевые предпочтения
- Аллергии / непереносимости: нет
- Не ем: ___
- Предпочитаю: ___
- Кухня: ___

## Приёмы пищи
- Завтрак: ~___:___
- Обед: ~___:___
- Ужин: ~___:___
- Перекусы: да / нет

## Заметки
- ___
```

- [ ] **Step 3: Create memory files**

```markdown
# memory/MEMORY.md
# Память агента

Этот файл — индекс памяти. Обновляй его при изменениях.

## Файлы
- eating_patterns.md — паттерны питания
- favorite_foods.md — частые продукты
- corrections.md — коррекции пользователя
- weekly_insights.md — выводы из анализов
```

Create empty starter files:

```markdown
# memory/eating_patterns.md
# Паттерны питания
```

```markdown
# memory/favorite_foods.md
# Частые продукты
```

```markdown
# memory/corrections.md
# Коррекции
```

```markdown
# memory/weekly_insights.md
# Выводы из анализов
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md about_me.md memory/
git commit -m "feat: add CLAUDE.md instructions, user profile template, and memory files"
```

---

### Task 12: Agent Skills

**Files:**
- Create: `.claude/skills/quick-log/SKILL.md`
- Create: `.claude/skills/nutrition-analysis/SKILL.md`
- Create: `.claude/skills/weight-dynamics/SKILL.md`
- Create: `.claude/skills/meal-planner/SKILL.md`
- Create: `.claude/skills/daily-menu/SKILL.md`
- Create: `.claude/skills/workout-planner/SKILL.md`
- Create: `.claude/skills/workout-analysis/SKILL.md`
- Create: `.claude/skills/weekly-report/SKILL.md`

- [ ] **Step 1: Create quick-log skill**

```markdown
<!-- .claude/skills/quick-log/SKILL.md -->
---
name: quick-log
description: Быстрое добавление еды в дневник. Используй когда пользователь говорит что съел, отправляет фото еды или баркод.
---

## Алгоритм

1. Определи еду (из текста, фото или баркода)
2. Найди в FatSecret через fatsecret_food_search или fatsecret_food_barcode_scan
3. Покажи пользователю найденный продукт с КБЖУ
4. Спроси подтверждение: порция, приём пищи (завтрак/обед/ужин/перекус)
5. Добавь в дневник через fatsecret_diary_add_entry
6. Покажи итог дня: сколько съедено, сколько осталось до цели

## Формат ответа

Продукт: {название}
Порция: {размер}
| Калории | Белки | Жиры | Углеводы |
|---------|-------|------|----------|
| {kcal}  | {p}г  | {f}г | {c}г     |

Добавить в {приём пищи}? (да/нет)
```

- [ ] **Step 2: Create nutrition-analysis skill**

```markdown
<!-- .claude/skills/nutrition-analysis/SKILL.md -->
---
name: nutrition-analysis
description: Анализ питания за период. Используй когда пользователь просит проанализировать питание, диету, рацион за день, неделю или месяц.
---

## Алгоритм

1. Определи период анализа (по умолчанию — последние 7 дней)
2. Получи данные через fatsecret_diary_get_month или fatsecret_diary_get_entries
3. Рассчитай средние значения КБЖУ за период
4. Прочитай цели из about_me.md
5. Сравни средние с целями
6. Определи паттерны: пропущенные приёмы, перекосы по макронутриентам
7. Если есть memory/eating_patterns.md — учти известные паттерны
8. Обнови memory/weekly_insights.md с новыми выводами

## Формат отчёта

### Сводка за {период}

| День | Калории | Белки | Жиры | Углеводы |
|------|---------|-------|------|----------|
| ... | ... | ... | ... | ... |

### Среднее vs Цель

| | Среднее | Цель | Отклонение |
|---|---------|------|-----------|
| Калории | {avg} | {target} | {diff}% |
| Белки | {avg}г | {target}г | {diff}% |
| Жиры | {avg}г | {target}г | {diff}% |
| Углеводы | {avg}г | {target}г | {diff}% |

### Проблемные зоны
- ...

### Рекомендации
- ...
```

- [ ] **Step 3: Create weight-dynamics skill**

```markdown
<!-- .claude/skills/weight-dynamics/SKILL.md -->
---
name: weight-dynamics
description: Анализ динамики веса. Используй когда пользователь спрашивает про прогресс веса, тренд, динамику.
---

## Алгоритм

1. Получи историю веса через fatsecret_weight_get_month (текущий + предыдущий месяц)
2. Определи тренд: набор / снижение / стагнация
3. Рассчитай среднюю скорость изменения (кг/неделю)
4. Прочитай целевой вес из about_me.md
5. Спрогнозируй дату достижения цели при текущем тренде
6. Если стагнация или движение не туда — предложи корректировку калоража

## Формат отчёта

### Динамика веса

| Дата | Вес (кг) | Изменение |
|------|----------|-----------|
| ... | ... | ... |

Текущий тренд: {тренд} ({скорость} кг/нед)
Цель: {target} кг
Прогноз достижения: {дата}

### Рекомендации
- ...
```

- [ ] **Step 4: Create meal-planner skill**

```markdown
<!-- .claude/skills/meal-planner/SKILL.md -->
---
name: meal-planner
description: Составление плана питания на неделю. Используй когда пользователь просит план питания, меню на неделю.
---

## Алгоритм

1. Прочитай цели и предпочтения из about_me.md
2. Прочитай memory/favorite_foods.md для учёта любимых продуктов
3. Прочитай memory/corrections.md для учёта коррекций
4. Составь 7-дневный план: завтрак, обед, ужин, перекусы
5. Для каждого блюда найди в FatSecret через fatsecret_food_search
6. Рассчитай КБЖУ на каждый день
7. Убедись что план попадает в целевой коридор (±10%)

## Формат

### План питания на неделю

#### Понедельник
| Приём | Блюдо | Калории | Б | Ж | У |
|-------|-------|---------|---|---|---|
| Завтрак | ... | ... | ... | ... | ... |
| Обед | ... | ... | ... | ... | ... |
| Ужин | ... | ... | ... | ... | ... |
| Итого | | {sum} | {sum} | {sum} | {sum} |

(повторить для каждого дня)
```

- [ ] **Step 5: Create daily-menu skill**

```markdown
<!-- .claude/skills/daily-menu/SKILL.md -->
---
name: daily-menu
description: Меню на сегодня с учётом уже съеденного. Используй когда пользователь спрашивает что есть сегодня, что осталось съесть.
---

## Алгоритм

1. Получи записи дневника за сегодня через fatsecret_diary_get_entries
2. Рассчитай уже потреблённые КБЖУ
3. Прочитай цели из about_me.md
4. Рассчитай оставшийся бюджет КБЖУ
5. Предложи блюда на оставшиеся приёмы пищи
6. Учитывай предпочтения из memory/favorite_foods.md

## Формат

### Уже съедено сегодня
| Приём | Блюдо | Кал | Б | Ж | У |
|-------|-------|-----|---|---|---|
| ... | ... | ... | ... | ... | ... |
| **Итого** | | **{sum}** | | | |

### Осталось до цели
| | Осталось | Цель |
|---|---------|------|
| Калории | {remaining} | {target} |

### Предлагаю на {приём}
- ...
```

- [ ] **Step 6: Create workout-planner skill**

```markdown
<!-- .claude/skills/workout-planner/SKILL.md -->
---
name: workout-planner
description: План тренировок. Используй когда пользователь спрашивает что делать в зале, план тренировки.
---

## Алгоритм

1. Прочитай about_me.md — цели, тип тренировок, частота
2. Получи историю упражнений через fatsecret_exercise_get_month
3. Определи какие группы мышц давно не тренировались
4. Предложи тренировку на сегодня с конкретными упражнениями
5. Укажи подходы, повторения, время

## Формат

### Тренировка на {дата}

| Упражнение | Подходы × Повторения | Отдых |
|-----------|---------------------|-------|
| ... | ... | ... |

Примерная длительность: {мин} мин
Примерный расход: {kcal} ккал
```

- [ ] **Step 7: Create workout-analysis skill**

```markdown
<!-- .claude/skills/workout-analysis/SKILL.md -->
---
name: workout-analysis
description: Анализ тренировок за период. Используй когда пользователь спрашивает про анализ тренировок, сколько сжёг, статистику упражнений.
---

## Алгоритм

1. Получи данные через fatsecret_exercise_get_month
2. Рассчитай: количество тренировок, общее время, калории
3. Сравни с целями из about_me.md
4. Определи самые частые упражнения
5. Рекомендуй корректировки

## Формат

### Анализ тренировок за {период}

| Показатель | Значение |
|-----------|----------|
| Тренировок | {count} |
| Общее время | {hours}ч {min}мин |
| Калорий сожжено | {kcal} |

### Рекомендации
- ...
```

- [ ] **Step 8: Create weekly-report skill**

```markdown
<!-- .claude/skills/weekly-report/SKILL.md -->
---
name: weekly-report
description: Полный еженедельный отчёт по питанию, весу и тренировкам. Используй когда пользователь просит отчёт за неделю, итоги недели.
---

## Алгоритм

1. Используй Skill nutrition-analysis для анализа питания за 7 дней
2. Используй Skill weight-dynamics для анализа веса
3. Используй Skill workout-analysis для анализа тренировок
4. Объедини всё в единый отчёт
5. Сформулируй план на следующую неделю
6. Обнови memory/weekly_insights.md с ключевыми выводами

## Формат

### Еженедельный отчёт: {дата начала} — {дата конца}

#### Питание
(таблица КБЖУ по дням + среднее vs цель)

#### Вес
(текущий, изменение за неделю, тренд)

#### Тренировки
(количество, время, калории)

#### Ключевые выводы
- ...

#### План на следующую неделю
- ...
```

- [ ] **Step 9: Commit all skills**

```bash
git add .claude/skills/
git commit -m "feat: add 8 agent skills for nutrition analysis, planning, and tracking"
```

---

### Task 13: Integration Test — End-to-End Smoke Test

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration smoke test**

```python
# tests/test_integration.py
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
```

- [ ] **Step 2: Run integration tests**

Run: `python -m pytest tests/test_integration.py -v`
Expected: All tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration smoke tests for nutrition agent"
```

---

## Summary

| Task | Description | Files | Estimated Steps |
|------|------------|-------|----------------|
| 1 | Dependencies + environment | 3 | 6 |
| 2 | Config module | 3 | 6 |
| 3 | Session manager | 3 | 6 |
| 4 | Barcode service | 2 | 5 |
| 5 | Whisper service | 2 | 5 |
| 6 | Agent SDK wrapper | 2 | 5 |
| 7 | Command handlers | 2 | 3 |
| 8 | Text + voice handlers | 2 | 3 |
| 9 | Photo handler | 1 | 2 |
| 10 | Bot assembly + entry point | 2 | 4 |
| 11 | CLAUDE.md + profile + memory | 7 | 4 |
| 12 | Agent skills (8 skills) | 8 | 9 |
| 13 | Integration smoke tests | 1 | 3 |
| **Total** | | **38 files** | **61 steps** |
