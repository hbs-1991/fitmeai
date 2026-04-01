from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from collections.abc import Awaitable, Callable

from claude_agent_sdk import (
    ClaudeAgentOptions,
    HookMatcher,
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

# Callback type: receives tool name when agent invokes a tool
OnToolUse = Callable[[str], Awaitable[None]]

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
        """Load about_me.md as extra context appended to claude_code preset.

        CLAUDE.md and Skills are loaded automatically by setting_sources=["project"].
        """
        about_me = self._project_dir / "about_me.md"
        if about_me.exists():
            return about_me.read_text(encoding="utf-8")
        return ""

    def _build_base_options(self) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            system_prompt={
                "type": "preset",
                "preset": "claude_code",
                "append": self._build_system_prompt(),
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
            max_budget_usd=1.0,
            debug_stderr=sys.stderr,
            hooks={
                "UserPromptSubmit": [
                    HookMatcher(matcher=".*", hooks=[self._load_memory])
                ]
            },
        )

    def _build_resume_options(self, session_id: str) -> ClaudeAgentOptions:
        opts = self._build_base_options()
        opts.resume = session_id
        return opts

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
        self,
        prompt: str,
        session_id: str | None = None,
        on_tool_use: OnToolUse | None = None,
    ) -> tuple[str, str | None]:
        """Send text prompt to agent. Returns (response_text, session_id)."""
        mode = "resume" if session_id else "new"
        logger.info("send_text [%s] session=%s prompt=%r", mode, session_id, prompt[:80])

        if session_id:
            options = self._build_resume_options(session_id)
        else:
            options = self._build_base_options()

        new_session_id: str | None = None
        result_text = ""
        msg_count = 0

        async for message in query(prompt=prompt, options=options):
            msg_count += 1
            msg_type = type(message).__name__

            if isinstance(message, SystemMessage):
                subtype = getattr(message, "subtype", None)
                logger.debug("SDK msg #%d: %s subtype=%s", msg_count, msg_type, subtype)
                if subtype == "init":
                    new_session_id = message.data.get("session_id") if hasattr(message, "data") and isinstance(message.data, dict) else None

            elif isinstance(message, AssistantMessage):
                for block in getattr(message, "content", []):
                    if isinstance(block, TextBlock):
                        result_text += block.text
                    elif isinstance(block, ToolUseBlock) and on_tool_use:
                        try:
                            await on_tool_use(block.name)
                        except Exception:
                            logger.debug("on_tool_use callback failed", exc_info=True)
                logger.debug("SDK msg #%d: AssistantMessage blocks=%d", msg_count, len(getattr(message, "content", [])))

            elif isinstance(message, ResultMessage):
                final = getattr(message, "result", None)
                if final:
                    result_text = final
                logger.info("send_text completed: %d messages, result_len=%d", msg_count, len(result_text))

            else:
                logger.debug("SDK msg #%d: %s", msg_count, msg_type)

        return (result_text, new_session_id)

    async def send_image(
        self,
        image_path: str,
        text: str,
        session_id: str | None = None,
        on_tool_use: OnToolUse | None = None,
    ) -> tuple[str, str | None]:
        """Send image + text to agent. Returns (response_text, session_id)."""
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
        result_text = ""
        msg_count = 0

        async for message in query(prompt=message_stream(), options=options):
            msg_count += 1

            if isinstance(message, SystemMessage):
                if hasattr(message, "subtype") and message.subtype == "init":
                    new_session_id = message.data.get("session_id") if hasattr(message, "data") and isinstance(message.data, dict) else None

            elif isinstance(message, AssistantMessage):
                for block in getattr(message, "content", []):
                    if isinstance(block, TextBlock):
                        result_text += block.text
                    elif isinstance(block, ToolUseBlock) and on_tool_use:
                        try:
                            await on_tool_use(block.name)
                        except Exception:
                            logger.debug("on_tool_use callback failed", exc_info=True)

            elif isinstance(message, ResultMessage):
                final = getattr(message, "result", None)
                if final:
                    result_text = final
                logger.info("send_image completed: %d messages", msg_count)

        return (result_text, new_session_id)
