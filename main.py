import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.bot.handlers import get_handlers_router
from app.config import get_settings


def configure_logging() -> None:
    """Configure application logging."""

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )


async def main() -> None:
    """Configure and start the Telegram bot."""

    configure_logging()

    settings = get_settings()

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
    )

    dispatcher = Dispatcher()
    dispatcher.include_router(get_handlers_router())

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())