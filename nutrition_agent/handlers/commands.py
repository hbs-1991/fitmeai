from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from nutrition_agent.services.session_manager import SessionManager

router = Router()

_sessions: SessionManager | None = None


def setup(sessions: SessionManager) -> None:
    global _sessions
    _sessions = sessions


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! Я твой персональный нутрициолог и фитнес-тренер.\n\n"
        "Что я умею:\n"
        "- Отправь фото еды — я распознаю и добавлю в дневник\n"
        "- Отправь фото баркода — найду продукт\n"
        "- Отправь голосовое — пойму и обработаю\n"
        "- Напиши что съел — добавлю в дневник\n\n"
        "Команды:\n"
        "/help — справка\n"
        "/profile — показать профиль\n"
        "/newsession — начать новый диалог\n"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Просто напиши мне:\n"
        "- «Я съел 200г куриной грудки» — запишу в дневник\n"
        "- «Проанализируй мое питание за неделю» — анализ\n"
        "- «Составь план питания» — план на неделю\n"
        "- «Что мне есть сегодня?» — меню на день\n"
        "- «Динамика веса» — прогресс по весу\n"
        "- «Отчет за неделю» — полный отчет\n"
    )


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    from nutrition_agent.config import PROJECT_DIR

    profile_path = PROJECT_DIR / "about_me.md"
    if profile_path.exists():
        content = profile_path.read_text(encoding="utf-8")
        await message.answer(content[:4096])
    else:
        await message.answer("Профиль не найден. Создай файл about_me.md в корне проекта.")


@router.message(Command("newsession"))
async def cmd_new_session(message: Message) -> None:
    if _sessions:
        _sessions.clear_session(message.chat.id, message.message_thread_id)
    await message.answer("Начинаю новый диалог. Предыдущий контекст сброшен.")
