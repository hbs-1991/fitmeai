from __future__ import annotations

import asyncio
import logging
import re
from html import escape as html_escape

from aiogram import Bot
from aiogram.types import Message

logger = logging.getLogger(__name__)

TELEGRAM_MAX_LENGTH = 4096

# ── Tool name → human-readable label mapping ────────────────────────────────

_TOOL_LABELS: dict[str, str] = {
    # Agent SDK built-in tools
    "Read": "📖 Читаю файл",
    "Write": "📝 Записываю файл",
    "Skill": "🧠 Использую навык",
    # Photo handler pseudo-tool
    "barcode_lookup": "📷 Сканирую баркод",
    # FatSecret MCP tools — foods
    "mcp__fatsecret__fatsecret_food_search": "🔍 Ищу продукт",
    "mcp__fatsecret__fatsecret_food_get": "📋 Загружаю продукт",
    "mcp__fatsecret__fatsecret_food_autocomplete": "🔍 Подбираю варианты",
    "mcp__fatsecret__fatsecret_food_search_v3": "🔍 Ищу продукт",
    "mcp__fatsecret__fatsecret_food_barcode_scan": "📷 Ищу по баркоду",
    "mcp__fatsecret__fatsecret_food_create": "➕ Создаю продукт",
    "mcp__fatsecret__fatsecret_recipe_search": "🍳 Ищу рецепт",
    "mcp__fatsecret__fatsecret_recipe_get": "🍳 Загружаю рецепт",
    # FatSecret MCP tools — diary
    "mcp__fatsecret__fatsecret_diary_get_entries": "📖 Читаю дневник",
    "mcp__fatsecret__fatsecret_diary_get_month": "📅 Загружаю месяц",
    "mcp__fatsecret__fatsecret_diary_add_entry": "✏️ Записываю в дневник",
    "mcp__fatsecret__fatsecret_diary_edit_entry": "✏️ Редактирую запись",
    "mcp__fatsecret__fatsecret_diary_delete_entry": "🗑 Удаляю запись",
    # FatSecret MCP tools — exercise
    "mcp__fatsecret__fatsecret_exercise_search": "🏋️ Ищу упражнение",
    "mcp__fatsecret__fatsecret_exercise_get_entries": "🏋️ Читаю тренировки",
    "mcp__fatsecret__fatsecret_exercise_get_month": "📅 Тренировки за месяц",
    "mcp__fatsecret__fatsecret_exercise_add_entry": "🏋️ Записываю тренировку",
    "mcp__fatsecret__fatsecret_exercise_edit_entry": "🏋️ Редактирую тренировку",
    # FatSecret MCP tools — weight
    "mcp__fatsecret__fatsecret_weight_update": "⚖️ Обновляю вес",
    "mcp__fatsecret__fatsecret_weight_get_month": "⚖️ Вес за месяц",
}


def tool_display_name(tool_name: str) -> str:
    """Convert internal tool name to a user-friendly label."""
    if tool_name in _TOOL_LABELS:
        return _TOOL_LABELS[tool_name]
    # Fallback for unknown MCP tools
    if tool_name.startswith("mcp__fatsecret__"):
        short = tool_name.removeprefix("mcp__fatsecret__fatsecret_").replace("_", " ")
        return f"🍎 FatSecret: {short}"
    return f"🔧 {tool_name}"


# ── Status message (editable "thinking" indicator) ───────────────────────────


class StatusMessage:
    """Manages a single Telegram message that shows agent activity.

    - Created with "thinking" text on enter
    - Updated in-place when tools are called
    - Deleted when the agent finishes (on exit / close)
    """

    THINKING = "💭 Думаю..."

    def __init__(self, bot: Bot, chat_id: int) -> None:
        self._bot = bot
        self._chat_id = chat_id
        self._message_id: int | None = None
        self._current_text: str = ""
        self._lock = asyncio.Lock()

    async def show(self) -> None:
        """Send the initial status message."""
        try:
            msg = await self._bot.send_message(self._chat_id, self.THINKING)
            self._message_id = msg.message_id
            self._current_text = self.THINKING
        except Exception:
            logger.debug("Failed to send status message", exc_info=True)

    async def update(self, tool_name: str) -> None:
        """Update status to show which tool is being used."""
        if not self._message_id:
            return
        label = tool_display_name(tool_name)
        new_text = f"⏳ {label}..."
        if new_text == self._current_text:
            return
        async with self._lock:
            try:
                await self._bot.edit_message_text(
                    new_text, chat_id=self._chat_id, message_id=self._message_id
                )
                self._current_text = new_text
            except Exception:
                logger.debug("Failed to edit status message", exc_info=True)

    async def close(self) -> None:
        """Delete the status message when agent is done."""
        if not self._message_id:
            return
        try:
            await self._bot.delete_message(self._chat_id, self._message_id)
        except Exception:
            logger.debug("Failed to delete status message", exc_info=True)
        self._message_id = None

# ── Markdown table → Unicode box-drawing ──────────────────────────────────


def _parse_md_table(lines: list[str]) -> list[list[str]] | None:
    """Parse consecutive Markdown table lines into a list of rows (list of cells).

    Returns None if *lines* do not form a valid Markdown table.
    A valid table has:
      - at least 2 lines (header + separator)
      - a separator line matching  |? *:?-+:? *| ...
    """
    if len(lines) < 2:
        return None

    rows: list[list[str]] = []
    sep_idx: int | None = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|") and "|" not in stripped:
            return None

        cells = [c.strip() for c in stripped.strip("|").split("|")]

        # Detect separator row  (--- or :---: etc.)
        if sep_idx is None and all(re.fullmatch(r":?-{1,}:?", c.strip()) for c in cells if c.strip()):
            sep_idx = i
            continue

        rows.append(cells)

    if sep_idx is None:
        return None
    return rows


def _render_box_table(rows: list[list[str]]) -> str:
    """Render rows as a Unicode box-drawing table string."""
    if not rows:
        return ""

    # Normalise column count
    n_cols = max(len(r) for r in rows)
    for r in rows:
        while len(r) < n_cols:
            r.append("")

    # Column widths (min 3 for aesthetics)
    widths = [max(3, *(len(r[c]) for r in rows)) for c in range(n_cols)]

    def hline(left: str, mid: str, right: str, fill: str = "─") -> str:
        return left + mid.join(fill * (w + 2) for w in widths) + right

    top = hline("┌", "┬", "┐")
    sep = hline("├", "┼", "┤")
    bot = hline("└", "┴", "┘")

    def data_line(row: list[str]) -> str:
        cells = " │ ".join(cell.ljust(w) for cell, w in zip(row, widths))
        return f"│ {cells} │"

    parts = [top]
    for idx, row in enumerate(rows):
        parts.append(data_line(row))
        if idx == 0 and len(rows) > 1:
            parts.append(sep)
    parts.append(bot)
    return "\n".join(parts)


# ── Markdown → Telegram HTML converter ────────────────────────────────────

# Placeholders for protected regions (code blocks / inline code)
_PH_PREFIX = "\x00PH"
_PH_SUFFIX = "\x00"


def markdown_to_telegram_html(text: str) -> str:
    """Convert an LLM Markdown response to Telegram-safe HTML.

    Handles:
    - Fenced code blocks (``` … ```)  →  <pre>…</pre>
    - Inline code (`…`)               →  <code>…</code>
    - Markdown tables (| … |)         →  <pre> Unicode box table </pre>
    - Bold (**…** / __…__)            →  <b>…</b>
    - Italic (*…* / _…_)             →  <i>…</i>
    - Strikethrough (~~…~~)           →  <s>…</s>
    - Headers (### …)                 →  <b>…</b>
    - HTML special chars              →  escaped
    """
    protected: list[str] = []

    def _protect(html_fragment: str) -> str:
        idx = len(protected)
        protected.append(html_fragment)
        return f"{_PH_PREFIX}{idx}{_PH_SUFFIX}"

    def _restore(t: str) -> str:
        def _repl(m: re.Match) -> str:
            return protected[int(m.group(1))]
        return re.sub(rf"{_PH_PREFIX}(\d+){_PH_SUFFIX}", _repl, t)

    # 1. Extract fenced code blocks ``` ... ```
    def _replace_fenced(m: re.Match) -> str:
        code = html_escape(m.group(2))
        return _protect(f"<pre>{code}</pre>")

    text = re.sub(r"```(\w*)\n?(.*?)```", _replace_fenced, text, flags=re.DOTALL)

    # 2. Extract inline code `...`
    def _replace_inline_code(m: re.Match) -> str:
        code = html_escape(m.group(1))
        return _protect(f"<code>{code}</code>")

    text = re.sub(r"`([^`\n]+)`", _replace_inline_code, text)

    # 3. Convert Markdown tables → box-drawing inside <pre>
    out_lines: list[str] = []
    table_buf: list[str] = []

    def _flush_table() -> None:
        if not table_buf:
            return
        rows = _parse_md_table(table_buf)
        if rows:
            box = _render_box_table(rows)
            out_lines.append(_protect(f"<pre>{html_escape(box)}</pre>"))
        else:
            out_lines.extend(table_buf)
        table_buf.clear()

    for line in text.split("\n"):
        stripped = line.strip()
        # A table line must contain a pipe
        if "|" in stripped and not stripped.startswith(_PH_PREFIX):
            table_buf.append(line)
        else:
            _flush_table()
            out_lines.append(line)
    _flush_table()

    text = "\n".join(out_lines)

    # 4. Escape HTML special chars in remaining text
    #    (placeholders are safe — they don't contain < > &)
    text = html_escape(text)

    # 5. Markdown formatting → HTML tags
    # Bold: **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
    # Strikethrough: ~~text~~
    text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text)
    # Italic: *text* or _text_  (but not inside words like some_var_name)
    text = re.sub(r"(?<!\w)\*([^\*\n]+?)\*(?!\w)", r"<i>\1</i>", text)
    text = re.sub(r"(?<!\w)_([^_\n]+?)_(?!\w)", r"<i>\1</i>", text)
    # Headers: ### Header → bold
    text = re.sub(r"^#{1,6}\s+(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)

    # 6. Restore protected regions
    text = _restore(text)

    return text


# ── Telegram message sender ───────────────────────────────────────────────


async def send_long_text(message: Message, text: str) -> None:
    """Convert Markdown to Telegram HTML and send, splitting at 4096 chars."""
    if not text:
        await message.answer("Не удалось получить ответ. Попробуй ещё раз.")
        return

    html = markdown_to_telegram_html(text)

    for i in range(0, len(html), TELEGRAM_MAX_LENGTH):
        await message.answer(html[i : i + TELEGRAM_MAX_LENGTH])
