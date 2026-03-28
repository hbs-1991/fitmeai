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

    def _build_system_prompt(self) -> str:
        """Load CLAUDE.md + about_me.md as the system prompt."""
        parts: list[str] = []

        claude_md = self._project_dir / "CLAUDE.md"
        if claude_md.exists():
            parts.append(claude_md.read_text(encoding="utf-8"))

        about_me = self._project_dir / "about_me.md"
        if about_me.exists():
            parts.append(about_me.read_text(encoding="utf-8"))

        return "\n\n".join(parts) if parts else ""

    def _build_base_options(self) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            system_prompt=self._build_system_prompt(),
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
                "mcp__fatsecret__*",
            ],
            max_turns=20,
            max_budget_usd=1.0,
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
        input_data: Any,
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
