from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.filters import IsAdmin
from app.bot.keyboards.admin import (
    ADMIN_PANEL_BUTTON,
    DISABLE_NOTIFICATIONS_BUTTON,
    ENABLE_NOTIFICATIONS_BUTTON,
    REFRESH_PANEL_BUTTON,
    USER_MODE_BUTTON,
    get_admin_keyboard,
)
from app.bot.keyboards.main_menu import (
    get_main_menu_keyboard,
)
from app.services.admin_service import (
    AdminPanelData,
    get_admin_panel_data,
    toggle_admin_notifications,
)


router = Router(name=__name__)


def build_admin_panel_text(
    data: AdminPanelData,
) -> str:
    """Build the administrator panel text."""

    notifications = (
        "включены"
        if data.notifications_enabled
        else "выключены"
    )

    return (
        "<b>Админ-панель</b>\n\n"
        f"<b>Новые заявки:</b> {data.new_leads}\n"
        f"<b>Активные заявки:</b> {data.active_leads}\n"
        f"<b>Закрытые заявки:</b> {data.closed_leads}\n\n"
        f"<b>Уведомления:</b> {notifications}"
    )


async def show_admin_panel(message: Message) -> None:
    """Show current administrator statistics."""

    user = message.from_user

    if user is None:
        return

    data = await get_admin_panel_data(user.id)

    await message.answer(
        build_admin_panel_text(data),
        parse_mode="HTML",
        reply_markup=get_admin_keyboard(
            notifications_enabled=(
                data.notifications_enabled
            ),
        ),
    )


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
) -> None:
    """Open the administrator panel."""

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
) -> None:
    """Return the administrator to the user menu."""

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