from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message


router = Router(name=__name__)


@router.message(CommandStart())
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