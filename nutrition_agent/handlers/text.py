from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Router
from aiogram.types import Message

from nutrition_agent.agent import NutritionAgent
from nutrition_agent.handlers.utils import StatusMessage, send_long_text
from nutrition_agent.services.session_manager import SessionManager

logger = logging.getLogger(__name__)

router = Router()

_agent: NutritionAgent | None = None
_sessions: SessionManager | None = None


def setup(agent: NutritionAgent, sessions: SessionManager) -> None:
    global _agent, _sessions
    _agent = agent
    _sessions = sessions


AGENT_TIMEOUT = 300  # seconds — max time to wait for agent response


@router.message()
async def handle_text(message: Message) -> None:
    if not message.text or not _agent or not _sessions:
        return

    chat_id = message.chat.id
    thread_id = message.message_thread_id
    session_id = _sessions.get_session(chat_id, thread_id)

    bot: Bot = message.bot  # type: ignore[assignment]

    status = StatusMessage(bot, chat_id, thread_id)
    await status.show()

    task = asyncio.create_task(
        _agent.send_text(
            prompt=message.text,
            session_id=session_id,
            on_tool_use=status.update,
        )
    )

    done, pending = await asyncio.wait({task}, timeout=AGENT_TIMEOUT)

    await status.close()

    if pending:
        task.cancel()
        logger.warning("Agent timed out after %ds for chat_id=%d", AGENT_TIMEOUT, chat_id)
        _sessions.clear_session(chat_id, thread_id)
        await message.answer(
            "Агент не ответил вовремя. Сессия сброшена — попробуй ещё раз."
        )
        return

    exc = task.exception() if not task.cancelled() else None
    if exc:
        logger.error("Agent error for chat_id=%d: %s", chat_id, exc)
        await message.answer("Произошла ошибка. Попробуй ещё раз.")
        return

    response_text, new_session_id = task.result()

    if new_session_id and new_session_id != session_id:
        _sessions.set_session(chat_id, new_session_id, thread_id)

    await send_long_text(message, response_text)
