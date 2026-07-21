from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.filters import IsAdmin
from app.bot.keyboards.admin import (
    ADMIN_PANEL_BUTTON,
    DISABLE_NOTIFICATIONS_BUTTON,
    ENABLE_NOTIFICATIONS_BUTTON,
    REFRESH_PANEL_BUTTON,
    USER_MODE_BUTTON,
)
from app.bot.keyboards.main_menu import get_main_menu_keyboard
from app.bot.views.admin_panel import show_admin_panel
from app.services.admin_service import (
    toggle_admin_notifications,
)


router = Router(name=__name__)


@router.message(
    IsAdmin(),
    Command("admin"),
)
@router.message(
    IsAdmin(),
    F.text == ADMIN_PANEL_BUTTON,
)
async def handle_admin_panel(
    message: Message,
    state: FSMContext,
) -> None:
    """Open the administrator panel."""

    await state.clear()
    await show_admin_panel(message)


@router.message(
    IsAdmin(),
    F.text == REFRESH_PANEL_BUTTON,
)
async def handle_refresh_panel(
    message: Message,
) -> None:
    """Refresh administrator statistics."""

    await show_admin_panel(message)


@router.message(
    IsAdmin(),
    F.text.in_(
        {
            ENABLE_NOTIFICATIONS_BUTTON,
            DISABLE_NOTIFICATIONS_BUTTON,
        }
    ),
)
async def handle_toggle_notifications(
    message: Message,
) -> None:
    """Toggle administrator notifications."""

    user = message.from_user

    if user is None:
        return

    await toggle_admin_notifications(user.id)
    await show_admin_panel(message)


@router.message(
    IsAdmin(),
    F.text == USER_MODE_BUTTON,
)
async def handle_user_mode(
    message: Message,
    state: FSMContext,
) -> None:
    """Return the administrator to the user menu."""

    await state.clear()

    await message.answer(
        "Включён пользовательский режим.",
        reply_markup=get_main_menu_keyboard(
            show_admin_panel=True,
        ),
    )


@router.message(Command("admin"))
async def handle_admin_access_denied(
    message: Message,
) -> None:
    """Reject unauthorized administrator access."""

    await message.answer(
        "У вас нет доступа к админ-панели."
    )
