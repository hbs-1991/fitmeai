from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from nutrition_agent.agent import NutritionAgent
from nutrition_agent.config import Config, PROJECT_DIR
from nutrition_agent.handlers import commands
from nutrition_agent.handlers import text
from nutrition_agent.handlers import voice
from nutrition_agent.handlers import photo
from nutrition_agent.services.session_manager import SessionManager

logger = logging.getLogger(__name__)


def create_bot(config: Config) -> tuple[Bot, Dispatcher]:
    bot = Bot(
        token=config.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher()

    # Services
    sessions = SessionManager(str(PROJECT_DIR / "sessions.json"))

    agent = NutritionAgent(
        project_dir=str(PROJECT_DIR),
        mcp_command=config.mcp_server_command,
        mcp_args=config.mcp_server_args,
        mcp_cwd=config.mcp_server_cwd,
    )

    # Inject dependencies into handlers
    text.setup(agent, sessions)
    voice.setup(agent, sessions)
    photo.setup(agent, sessions)

    # Register routers (order matters: commands first, then specific types, then text fallback)
    dp.include_router(commands.router)
    dp.include_router(voice.router)
    dp.include_router(photo.router)
    dp.include_router(text.router)

    return bot, dp
