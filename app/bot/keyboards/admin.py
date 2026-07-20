from collections.abc import Sequence

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.callbacks import (
    LeadOpenCallback,
    LeadPageCallback,
)
from app.database.models.lead import Lead

from app.bot.callbacks import (
    LeadOpenCallback,
    LeadPageCallback,
    LeadStatusCallback,
)

from app.database.enums import LeadStatus

ADMIN_PANEL_BUTTON = "Админ-панель"
NEW_LEADS_BUTTON = "Новые заявки"
ACTIVE_LEADS_BUTTON = "Активные заявки"
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
                KeyboardButton(text=NEW_LEADS_BUTTON),
                KeyboardButton(text=ACTIVE_LEADS_BUTTON),
            ],
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


def get_lead_list_keyboard(
    *,
    leads: Sequence[Lead],
    list_type: str,
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    """Return a paginated inline lead-list keyboard."""

    builder = InlineKeyboardBuilder()

    for lead in leads:
        title = lead.contact_name[:28]

        builder.button(
            text=(
                f"№{lead.id} · {title} · "
                f"{lead.created_at:%d.%m.%Y}"
            ),
            callback_data=LeadOpenCallback(
                lead_id=lead.id,
                list_type=list_type,
                page=page,
            ),
        )

    builder.adjust(1)

    navigation: list[InlineKeyboardButton] = []

    if page > 1:
        navigation.append(
            InlineKeyboardButton(
                text="← Назад",
                callback_data=LeadPageCallback(
                    list_type=list_type,
                    page=page - 1,
                ).pack(),
            )
        )

    if page < total_pages:
        navigation.append(
            InlineKeyboardButton(
                text="Вперёд →",
                callback_data=LeadPageCallback(
                    list_type=list_type,
                    page=page + 1,
                ).pack(),
            )
        )

    if navigation:
        builder.row(*navigation)

    return builder.as_markup()


def get_lead_card_keyboard(
    *,
    lead: Lead,
    list_type: str,
    page: int,
) -> InlineKeyboardMarkup:
    """Return actions available from a lead card."""

    builder = InlineKeyboardBuilder()
    user = lead.user

    if lead.status == LeadStatus.NEW:
        builder.row(
            InlineKeyboardButton(
                text="Взять в работу",
                callback_data=LeadStatusCallback(
                    lead_id=lead.id,
                    target_status=(
                        LeadStatus.IN_PROGRESS.value
                    ),
                    list_type=list_type,
                    page=page,
                ).pack(),
            )
        )

    if user.username:
        profile_url = f"https://t.me/{user.username}"
    else:
        profile_url = (
            f"tg://user?id={user.telegram_user_id}"
        )

    builder.row(
        InlineKeyboardButton(
            text="Связаться с клиентом",
            url=profile_url,
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="← Назад к списку",
            callback_data=LeadPageCallback(
                list_type=list_type,
                page=page,
            ).pack(),
        )
    )

    return builder.as_markup()