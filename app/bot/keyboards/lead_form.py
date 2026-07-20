from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

CANCEL_BUTTON = "Отменить"
SKIP_BUTTON = "Пропустить"
CONFIRM_BUTTON = "Подтвердить заявку"
RESTART_BUTTON = "Заполнить заново"

USE_PROFILE_NAME_BUTTON = "Использовать имя из профиля"
ENTER_CUSTOM_NAME_BUTTON = "Указать другое имя"
SHARE_CONTACT_BUTTON = "Поделиться контактом"


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Return a keyboard with the cancellation button."""

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=CANCEL_BUTTON)],
        ],
        resize_keyboard=True,
    )


def get_name_choice_keyboard() -> ReplyKeyboardMarkup:
    """Return a keyboard for choosing the client's display name."""

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=USE_PROFILE_NAME_BUTTON)],
            [KeyboardButton(text=ENTER_CUSTOM_NAME_BUTTON)],
            [KeyboardButton(text=CANCEL_BUTTON)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите вариант",
    )


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """Return a keyboard requesting the user's contact."""

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=SHARE_CONTACT_BUTTON,
                    request_contact=True,
                )
            ],
            [KeyboardButton(text=CANCEL_BUTTON)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Передайте контакт Telegram",
    )


def get_comment_keyboard() -> ReplyKeyboardMarkup:
    """Return a keyboard for the optional comment step."""

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=SKIP_BUTTON)],
            [KeyboardButton(text=CANCEL_BUTTON)],
        ],
        resize_keyboard=True,
    )


def get_confirmation_keyboard() -> ReplyKeyboardMarkup:
    """Return the lead confirmation keyboard."""

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=CONFIRM_BUTTON)],
            [KeyboardButton(text=RESTART_BUTTON)],
            [KeyboardButton(text=CANCEL_BUTTON)],
        ],
        resize_keyboard=True,
    )