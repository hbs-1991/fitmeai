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
    photo = message.photo[-1]
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

        async for text_chunk, new_session_id, result in send:
            if new_session_id and not session_id:
                session_id = new_session_id
                _sessions.set_session(chat_id, new_session_id, thread_id)

            if text_chunk:
                accumulated += text_chunk

        if accumulated:
            await message.answer(accumulated[:4096])

    finally:
        Path(tmp_path).unlink(missing_ok=True)
