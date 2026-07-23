from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards.main_menu import get_main_menu_keyboard
from app.services.admin_service import is_configured_admin


router = Router(name=__name__)


@router.message(CommandStart())
async def handle_start(
    message: Message,
    state: FSMContext,
) -> None:
    """Handle the /start command."""

    await state.clear()

    user = message.from_user

    first_name = (
        user.first_name
        if user
        else "пользователь"
    )

    show_admin_panel = bool(
        user
        and is_configured_admin(user.id)
    )

    await message.answer(
        f"Привет, {first_name}!\n\n"
        "Я Panini — Telegram-бот для знакомства с услугами "
        "и оформления клиентских заявок.\n\n"
        "Здесь можно узнать обо мне, посмотреть доступные "
        "услуги, изучить реализованный проект и оставить "
        "заявку на разработку собственного бота.\n\n"
        "Выберите нужный раздел в меню ниже.",
        reply_markup=get_main_menu_keyboard(
            show_admin_panel=show_admin_panel,
        ),
    )


@router.message(Command("myid"))
async def handle_my_id(message: Message) -> None:
    """Show the current user's Telegram ID."""

    user = message.from_user

    if user is None:
        await message.answer(
            "Не удалось определить Telegram ID."
        )
        return

    await message.answer(
        f"Ваш Telegram ID: <code>{user.id}</code>",
        parse_mode="HTML",
    )
