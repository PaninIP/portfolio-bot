from aiogram.enums import ButtonStyle
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.bot.keyboards.admin import ADMIN_PANEL_BUTTON


CANCEL_BUTTON = "❌ Отменить"
SKIP_BUTTON = "⏭ Пропустить"
CONFIRM_BUTTON = "✅ Подтвердить заявку"
RESTART_BUTTON = "🔄 Заполнить заново"
DONE_ATTACHMENTS_BUTTON = "✅ Готово"
SKIP_ATTACHMENTS_BUTTON = "⏭ Без вложений"

USE_PROFILE_NAME_BUTTON = "👤 Использовать имя из профиля"
ENTER_CUSTOM_NAME_BUTTON = "✏️ Указать другое имя"
SHARE_CONTACT_BUTTON = "📱 Поделиться контактом"


def append_admin_button(
    keyboard: list[list[KeyboardButton]],
    *,
    show_admin_panel: bool,
) -> None:
    """Append the administrator shortcut when available."""

    if show_admin_panel:
        keyboard.append(
            [
                KeyboardButton(
                    text=ADMIN_PANEL_BUTTON,
                    style=ButtonStyle.PRIMARY,
                )
            ]
        )


def get_cancel_keyboard(
    *,
    show_admin_panel: bool = False,
) -> ReplyKeyboardMarkup:
    """Return a keyboard with the cancellation button."""

    keyboard = [
        [
            KeyboardButton(
                text=CANCEL_BUTTON,
                style=ButtonStyle.DANGER,
            )
        ],
    ]

    append_admin_button(
        keyboard,
        show_admin_panel=show_admin_panel,
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def get_name_choice_keyboard(
    *,
    show_admin_panel: bool = False,
) -> ReplyKeyboardMarkup:
    """Return a keyboard for choosing the client's display name."""

    keyboard = [
        [
            KeyboardButton(
                text=USE_PROFILE_NAME_BUTTON,
                style=ButtonStyle.PRIMARY,
            )
        ],
        [
            KeyboardButton(
                text=ENTER_CUSTOM_NAME_BUTTON,
                style=ButtonStyle.PRIMARY,
            )
        ],
        [
            KeyboardButton(
                text=CANCEL_BUTTON,
                style=ButtonStyle.DANGER,
            )
        ],
    ]

    append_admin_button(
        keyboard,
        show_admin_panel=show_admin_panel,
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите вариант",
    )


def get_contact_keyboard(
    *,
    show_admin_panel: bool = False,
) -> ReplyKeyboardMarkup:
    """Return a keyboard requesting the user's contact."""

    keyboard = [
        [
            KeyboardButton(
                text=SHARE_CONTACT_BUTTON,
                request_contact=True,
                style=ButtonStyle.SUCCESS,
            )
        ],
        [
            KeyboardButton(
                text=CANCEL_BUTTON,
                style=ButtonStyle.DANGER,
            )
        ],
    ]

    append_admin_button(
        keyboard,
        show_admin_panel=show_admin_panel,
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Передайте контакт Telegram",
    )


def get_comment_keyboard(
    *,
    show_admin_panel: bool = False,
) -> ReplyKeyboardMarkup:
    """Return a keyboard for the optional comment step."""

    keyboard = [
        [
            KeyboardButton(
                text=SKIP_BUTTON,
                style=ButtonStyle.PRIMARY,
            )
        ],
        [
            KeyboardButton(
                text=CANCEL_BUTTON,
                style=ButtonStyle.DANGER,
            )
        ],
    ]

    append_admin_button(
        keyboard,
        show_admin_panel=show_admin_panel,
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def get_attachments_keyboard(
    *,
    show_admin_panel: bool = False,
) -> ReplyKeyboardMarkup:
    """Return controls for collecting optional lead attachments."""

    keyboard = [
        [
            KeyboardButton(
                text=DONE_ATTACHMENTS_BUTTON,
                style=ButtonStyle.SUCCESS,
            )
        ],
        [
            KeyboardButton(
                text=SKIP_ATTACHMENTS_BUTTON,
                style=ButtonStyle.PRIMARY,
            )
        ],
        [
            KeyboardButton(
                text=CANCEL_BUTTON,
                style=ButtonStyle.DANGER,
            )
        ],
    ]

    append_admin_button(
        keyboard,
        show_admin_panel=show_admin_panel,
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Отправьте материалы к проекту",
    )


def get_confirmation_keyboard(
    *,
    show_admin_panel: bool = False,
) -> ReplyKeyboardMarkup:
    """Return the lead confirmation keyboard."""

    keyboard = [
        [
            KeyboardButton(
                text=CONFIRM_BUTTON,
                style=ButtonStyle.SUCCESS,
            )
        ],
        [
            KeyboardButton(
                text=RESTART_BUTTON,
                style=ButtonStyle.PRIMARY,
            )
        ],
        [
            KeyboardButton(
                text=CANCEL_BUTTON,
                style=ButtonStyle.DANGER,
            )
        ],
    ]

    append_admin_button(
        keyboard,
        show_admin_panel=show_admin_panel,
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
