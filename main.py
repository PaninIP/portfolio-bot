import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.memory import SimpleEventIsolation

from app.bot.handlers import get_handlers_router
from app.config import get_settings


logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure application logging."""

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )


async def configure_bot_profile(bot: Bot) -> None:
    """Configure the public bot profile and command menu."""

    try:
        await bot.delete_my_commands()
        await bot.set_my_name(name="Panini")
        await bot.set_my_short_description(
            short_description=(
                "Panini — разработка Telegram-ботов "
                "и автоматизация бизнес-процессов."
            )
        )
        await bot.set_my_description(
            description=(
                "Panini помогает узнать об услугах по разработке "
                "Telegram-ботов и оформить заявку на новый проект."
            )
        )
    except TelegramAPIError:
        logger.exception(
            "Failed to configure the Telegram bot profile"
        )


async def main() -> None:
    """Configure and start the Telegram bot."""

    configure_logging()

    settings = get_settings()

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
    )

    dispatcher = Dispatcher(
        events_isolation=SimpleEventIsolation(),
    )
    dispatcher.include_router(get_handlers_router())

    try:
        await configure_bot_profile(bot)
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
