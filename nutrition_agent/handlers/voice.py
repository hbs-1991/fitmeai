from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

from aiogram import Bot, Router
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender

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


AGENT_TIMEOUT = 300


@router.message(lambda m: m.voice is not None)
async def handle_voice(message: Message) -> None:
    if not _agent or not _sessions:
        return

    bot: Bot = message.bot  # type: ignore[assignment]
    chat_id = message.chat.id
    thread_id = message.message_thread_id

    async with ChatActionSender.typing(bot=bot, chat_id=chat_id):
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

        task = asyncio.create_task(
            _agent.send_text(
                prompt=f"[Голосовое сообщение]: {text}", session_id=session_id
            ),
        )

        done, pending = await asyncio.wait({task}, timeout=AGENT_TIMEOUT)

        if pending:
            task.cancel()
            logger.warning("Agent timed out for voice message chat_id=%d", chat_id)
            _sessions.clear_session(chat_id, thread_id)
            await message.answer("Агент не ответил вовремя. Попробуй ещё раз.")
            return

        exc = task.exception() if not task.cancelled() else None
        if exc:
            logger.error("Agent error for voice chat_id=%d: %s", chat_id, exc)
            await message.answer("Произошла ошибка. Попробуй ещё раз.")
            return

        response_text, new_session_id = task.result()

        if new_session_id and new_session_id != session_id:
            _sessions.set_session(chat_id, new_session_id, thread_id)

        await send_long_text(message, response_text)
