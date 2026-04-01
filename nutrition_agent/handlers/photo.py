from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

from aiogram import Bot, Router
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender

from nutrition_agent.agent import NutritionAgent
from nutrition_agent.handlers.utils import StatusMessage, send_long_text
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


AGENT_TIMEOUT = 300


@router.message(lambda m: m.photo is not None)
async def handle_photo(message: Message) -> None:
    if not _agent or not _sessions:
        return

    bot: Bot = message.bot  # type: ignore[assignment]
    chat_id = message.chat.id
    thread_id = message.message_thread_id

    # Download phase — show typing indicator
    async with ChatActionSender.typing(bot=bot, chat_id=chat_id):
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            await bot.download_file(file.file_path, tmp.name)
            tmp_path = tmp.name

    session_id = _sessions.get_session(chat_id, thread_id)
    caption = message.caption or ""

    # Agent phase — show status message with tool indicators
    status = StatusMessage(bot, chat_id)
    await status.show()

    try:
        barcode = decode_barcode(tmp_path)

        if barcode:
            await status.update("barcode_lookup")
            prompt = f"Найди продукт по баркоду {barcode} и покажи информацию о питательной ценности"
            result = await asyncio.wait_for(
                _agent.send_text(
                    prompt=prompt,
                    session_id=session_id,
                    on_tool_use=status.update,
                ),
                timeout=AGENT_TIMEOUT,
            )
        else:
            text = caption or "Определи что за еда на фото, оцени порцию и предложи записать в дневник"
            result = await asyncio.wait_for(
                _agent.send_image(
                    image_path=tmp_path,
                    text=text,
                    session_id=session_id,
                    on_tool_use=status.update,
                ),
                timeout=AGENT_TIMEOUT,
            )

        await status.close()

        response_text, new_session_id = result

        if new_session_id and new_session_id != session_id:
            _sessions.set_session(chat_id, new_session_id, thread_id)

        await send_long_text(message, response_text)

    except asyncio.TimeoutError:
        await status.close()
        logger.warning("Agent timed out for photo chat_id=%d", chat_id)
        _sessions.clear_session(chat_id, thread_id)
        await message.answer("Агент не ответил вовремя. Попробуй ещё раз.")

    except Exception as exc:
        await status.close()
        logger.error("Agent error for photo chat_id=%d: %s", chat_id, exc)
        await message.answer("Произошла ошибка. Попробуй ещё раз.")

    finally:
        Path(tmp_path).unlink(missing_ok=True)
