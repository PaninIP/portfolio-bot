from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from app.bot.keyboards.admin import ADMIN_PANEL_BUTTON

ABOUT_BUTTON = "Обо мне"
SERVICES_BUTTON = "Услуги"
PORTFOLIO_BUTTON = "Примеры работ"
DISCUSS_PROJECT_BUTTON = "Обсудить проект"



def get_main_menu_keyboard(
    *,
    show_admin_panel: bool = False,
) -> ReplyKeyboardMarkup:
    """Return the main menu keyboard."""

    keyboard = [
        [
            KeyboardButton(text=ABOUT_BUTTON),
            KeyboardButton(text=SERVICES_BUTTON),
        ],
        [
            KeyboardButton(text=PORTFOLIO_BUTTON),
        ],
        [
            KeyboardButton(text=DISCUSS_PROJECT_BUTTON),
        ],
    ]

    if show_admin_panel:
        keyboard.append(
            [
                KeyboardButton(
                    text=ADMIN_PANEL_BUTTON,
                )
            ]
        )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел",
    )