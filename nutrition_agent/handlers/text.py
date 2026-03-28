from __future__ import annotations

import logging

from aiogram import Bot, Router
from aiogram.types import Message

from nutrition_agent.agent import NutritionAgent
from nutrition_agent.services.session_manager import SessionManager

logger = logging.getLogger(__name__)

router = Router()

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

    await bot.send_chat_action(chat_id=chat_id, action="typing")

    accumulated = ""

    async for text_chunk, new_session_id, result in _agent.send_text(
        prompt=message.text, session_id=session_id
    ):
        if new_session_id and not session_id:
            session_id = new_session_id
            _sessions.set_session(chat_id, new_session_id, thread_id)

        if text_chunk:
            accumulated += text_chunk

    if accumulated:
        await message.answer(accumulated[:4096])
    else:
        await message.answer("Не удалось получить ответ. Попробуй ещё раз.")
