from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


ABOUT_BUTTON = "Обо мне"
SERVICES_BUTTON = "Услуги"
PORTFOLIO_BUTTON = "Примеры работ"
DISCUSS_PROJECT_BUTTON = "Обсудить проект"


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Return the main menu keyboard."""

    return ReplyKeyboardMarkup(
        keyboard=[
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
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел",
    )