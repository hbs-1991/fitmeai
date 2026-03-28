from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from aiogram import Bot, Router
from aiogram.types import Message

from nutrition_agent.agent import NutritionAgent
from nutrition_agent.handlers.utils import send_long_text
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

    async for text_chunk, new_session_id, result in _agent.send_text(
        prompt=f"[Голосовое сообщение]: {text}", session_id=session_id
    ):
        if new_session_id and not session_id:
            session_id = new_session_id
            _sessions.set_session(chat_id, new_session_id, thread_id)

        if text_chunk:
            accumulated += text_chunk

    await send_long_text(message, accumulated)
