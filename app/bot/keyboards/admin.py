from __future__ import annotations

from collections.abc import Sequence

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.callbacks import (
    LeadCloseCallback,
    LeadCloseDecisionCallback,
    LeadOpenCallback,
    LeadPageCallback,
    LeadStatusCallback,
)
from app.database.enums import LeadStatus
from app.database.models.lead import Lead

ADMIN_PANEL_BUTTON = "Админ-панель"
NEW_LEADS_BUTTON = "Новые заявки"
ACTIVE_LEADS_BUTTON = "Активные заявки"
REFRESH_PANEL_BUTTON = "Обновить статистику"
ENABLE_NOTIFICATIONS_BUTTON = "Включить уведомления"
DISABLE_NOTIFICATIONS_BUTTON = "Отключить уведомления"
USER_MODE_BUTTON = "Пользовательский режим"
ARCHIVE_BUTTON = "Архив"
CLOSE_LEAD_BUTTON = "Закрыть заявку"
CANCEL_CLOSE_BUTTON = "Отменить закрытие"


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
            [
                KeyboardButton(text=NEW_LEADS_BUTTON),
                KeyboardButton(text=ACTIVE_LEADS_BUTTON),
            ],
            [
                KeyboardButton(text=ARCHIVE_BUTTON),
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

    if lead.status != LeadStatus.CLOSED:
        builder.row(
        InlineKeyboardButton(
            text=CLOSE_LEAD_BUTTON,
            callback_data=LeadCloseCallback(
                lead_id=lead.id,
                list_type=list_type,
                page=page,
            ).pack(),
        )
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

def get_close_comment_keyboard() -> ReplyKeyboardMarkup:
    """Return a keyboard for cancelling lead closure."""

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=CANCEL_CLOSE_BUTTON,
                )
            ]
        ],
        resize_keyboard=True,
    )


def get_close_confirmation_keyboard(
    *,
    lead_id: int,
    list_type: str,
    page: int,
) -> InlineKeyboardMarkup:
    """Return lead-closing confirmation actions."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Подтвердить закрытие",
                    callback_data=(
                        LeadCloseDecisionCallback(
                            action="confirm",
                            lead_id=lead_id,
                            list_type=list_type,
                            page=page,
                        ).pack()
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отменить",
                    callback_data=(
                        LeadCloseDecisionCallback(
                            action="cancel",
                            lead_id=lead_id,
                            list_type=list_type,
                            page=page,
                        ).pack()
                    ),
                )
            ],
        ]
    )