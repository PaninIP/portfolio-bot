import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.config import get_settings


dispatcher = Dispatcher()


@dispatcher.message(CommandStart())
async def handle_start(message: Message) -> None:
    """Handle the /start command."""

    first_name = (
        message.from_user.first_name
        if message.from_user
        else "пользователь"
    )

    await message.answer(
        f"Привет, {first_name}!\n\n"
        "Я бот-помощник Ивана Панина.\n"
        "Здесь можно узнать об услугах по разработке Telegram-ботов "
        "и оставить заявку на создание проекта.\n\n"
        "Сейчас бот находится в разработке."
    )


async def main() -> None:
    """Start the Telegram bot using long polling."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    settings = get_settings()

    bot = Bot(token=settings.bot_token.get_secret_value())

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())