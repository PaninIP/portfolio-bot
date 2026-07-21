from aiogram.types import Message

from app.bot.keyboards.admin import get_admin_keyboard
from app.services.admin_service import (
    AdminPanelData,
    get_admin_panel_data,
)


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
