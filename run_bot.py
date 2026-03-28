import asyncio
import logging

from nutrition_agent.bot import create_bot
from nutrition_agent.config import Config


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = Config()
    bot, dp = create_bot(config)

    async def start():
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    logging.info("Starting Nutrition Agent bot...")
    asyncio.run(start())


if __name__ == "__main__":
    main()
