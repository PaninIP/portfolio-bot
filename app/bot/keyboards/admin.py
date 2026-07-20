from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


ADMIN_PANEL_BUTTON = "Админ-панель"
REFRESH_PANEL_BUTTON = "Обновить статистику"
ENABLE_NOTIFICATIONS_BUTTON = "Включить уведомления"
DISABLE_NOTIFICATIONS_BUTTON = "Отключить уведомления"
USER_MODE_BUTTON = "Пользовательский режим"


def get_admin_keyboard(
    *,
    notifications_enabled: bool,
) -> ReplyKeyboardMarkup:
    """Return the administrator panel keyboard."""

    notification_button = (
        DISABLE_NOTIFICATIONS_BUTTON
        if notifications_enabled
        else ENABLE_NOTIFICATIONS_BUTTON
    )

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=REFRESH_PANEL_BUTTON,
                ),
            ],
            [
                KeyboardButton(
                    text=notification_button,
                ),
            ],
            [
                KeyboardButton(
                    text=USER_MODE_BUTTON,
                ),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Админ-панель",
    )