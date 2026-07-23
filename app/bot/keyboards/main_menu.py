from aiogram.enums import ButtonStyle
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.bot.keyboards.admin import ADMIN_PANEL_BUTTON


ABOUT_BUTTON = "👤 Обо мне"
SERVICES_BUTTON = "🛠 Услуги"
PORTFOLIO_BUTTON = "📂 Портфолио"
LEAVE_APPLICATION_BUTTON = "📝 Оставить заявку"


def get_main_menu_keyboard(
    *,
    show_admin_panel: bool = False,
) -> ReplyKeyboardMarkup:
    """Return the main menu keyboard."""

    keyboard = [
        [
            KeyboardButton(
                text=ABOUT_BUTTON,
                style=ButtonStyle.PRIMARY,
            ),
            KeyboardButton(
                text=SERVICES_BUTTON,
                style=ButtonStyle.PRIMARY,
            ),
        ],
        [
            KeyboardButton(
                text=PORTFOLIO_BUTTON,
                style=ButtonStyle.PRIMARY,
            ),
        ],
        [
            KeyboardButton(
                text=LEAVE_APPLICATION_BUTTON,
                style=ButtonStyle.SUCCESS,
            ),
        ],
    ]

    if show_admin_panel:
        keyboard.append(
            [
                KeyboardButton(
                    text=ADMIN_PANEL_BUTTON,
                    style=ButtonStyle.PRIMARY,
                )
            ]
        )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел",
    )
