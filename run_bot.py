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

    logging.info("Starting Nutrition Agent bot...")
    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
