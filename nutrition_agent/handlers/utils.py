from __future__ import annotations

from aiogram.types import Message

TELEGRAM_MAX_LENGTH = 4096


async def send_long_text(message: Message, text: str) -> None:
    """Send text that may exceed Telegram's 4096 char limit by splitting into chunks."""
    if not text:
        await message.answer("Не удалось получить ответ. Попробуй ещё раз.")
        return

    for i in range(0, len(text), TELEGRAM_MAX_LENGTH):
        await message.answer(text[i : i + TELEGRAM_MAX_LENGTH])
