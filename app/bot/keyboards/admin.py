from __future__ import annotations

from collections.abc import Sequence

from aiogram.enums import ButtonStyle
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
    LeadDatePresetCallback,
    LeadOpenCallback,
    LeadPageCallback,
    LeadReopenCallback,
    LeadResultOpenCallback,
    LeadResultPageCallback,
    LeadStatusCallback,
)
from app.database.enums import LeadStatus
from app.database.models.lead import Lead


ADMIN_PANEL_BUTTON = "⚙️ Админ-панель"
NEW_LEADS_BUTTON = "🆕 Новые заявки"
ACTIVE_LEADS_BUTTON = "📂 Активные заявки"
ARCHIVE_BUTTON = "🗄 Архив"
SEARCH_LEADS_BUTTON = "🔎 Найти заявку"
DATE_FILTER_BUTTON = "📅 Фильтр по датам"
REFRESH_PANEL_BUTTON = "🔄 Обновить статистику"
ENABLE_NOTIFICATIONS_BUTTON = "🔔 Включить уведомления"
DISABLE_NOTIFICATIONS_BUTTON = "🔕 Отключить уведомления"
USER_MODE_BUTTON = "👤 Пользовательский режим"
CLOSE_LEAD_BUTTON = "🔒 Закрыть заявку"
REOPEN_LEAD_BUTTON = "♻️ Вернуть в работу"
CANCEL_CLOSE_BUTTON = "↩️ Отменить закрытие"


STATUS_ICONS = {
    LeadStatus.NEW: "🆕",
    LeadStatus.IN_PROGRESS: "▶️",
    LeadStatus.WAITING_FOR_CLIENT: "⏳",
    LeadStatus.CLOSED: "✅",
}


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
    notification_style = (
        ButtonStyle.DANGER
        if notifications_enabled
        else ButtonStyle.SUCCESS
    )

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=NEW_LEADS_BUTTON,
                    style=ButtonStyle.PRIMARY,
                ),
                KeyboardButton(
                    text=ACTIVE_LEADS_BUTTON,
                    style=ButtonStyle.PRIMARY,
                ),
            ],
            [
                KeyboardButton(
                    text=ARCHIVE_BUTTON,
                    style=ButtonStyle.PRIMARY,
                ),
            ],
            [
                KeyboardButton(
                    text=SEARCH_LEADS_BUTTON,
                    style=ButtonStyle.PRIMARY,
                ),
                KeyboardButton(
                    text=DATE_FILTER_BUTTON,
                    style=ButtonStyle.PRIMARY,
                ),
            ],
            [
                KeyboardButton(
                    text=REFRESH_PANEL_BUTTON,
                    style=ButtonStyle.PRIMARY,
                ),
            ],
            [
                KeyboardButton(
                    text=notification_button,
                    style=notification_style,
                ),
            ],
            [
                KeyboardButton(
                    text=USER_MODE_BUTTON,
                    style=ButtonStyle.PRIMARY,
                ),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
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
            style=ButtonStyle.PRIMARY,
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
                style=ButtonStyle.PRIMARY,
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
                style=ButtonStyle.PRIMARY,
            )
        )

    if navigation:
        builder.row(*navigation)

    return builder.as_markup()


def get_lead_result_keyboard(
    *,
    leads: Sequence[Lead],
    mode: str,
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    """Return search or date-filter results with pagination."""

    builder = InlineKeyboardBuilder()

    for lead in leads:
        title = lead.contact_name[:24]
        status_icon = STATUS_ICONS.get(lead.status, "•")

        builder.button(
            text=(
                f"{status_icon} №{lead.id} · {title} · "
                f"{lead.created_at:%d.%m.%Y}"
            ),
            callback_data=LeadResultOpenCallback(
                mode=mode,
                lead_id=lead.id,
                page=page,
            ),
            style=ButtonStyle.PRIMARY,
        )

    builder.adjust(1)

    navigation: list[InlineKeyboardButton] = []

    if page > 1:
        navigation.append(
            InlineKeyboardButton(
                text="← Назад",
                callback_data=LeadResultPageCallback(
                    mode=mode,
                    page=page - 1,
                ).pack(),
                style=ButtonStyle.PRIMARY,
            )
        )

    if page < total_pages:
        navigation.append(
            InlineKeyboardButton(
                text="Вперёд →",
                callback_data=LeadResultPageCallback(
                    mode=mode,
                    page=page + 1,
                ).pack(),
                style=ButtonStyle.PRIMARY,
            )
        )

    if navigation:
        builder.row(*navigation)

    return builder.as_markup()


def get_date_filter_keyboard() -> InlineKeyboardMarkup:
    """Return predefined and custom date-filter actions."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Сегодня",
                    callback_data=LeadDatePresetCallback(
                        preset="today"
                    ).pack(),
                    style=ButtonStyle.PRIMARY,
                ),
                InlineKeyboardButton(
                    text="7 дней",
                    callback_data=LeadDatePresetCallback(
                        preset="7d"
                    ).pack(),
                    style=ButtonStyle.PRIMARY,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="30 дней",
                    callback_data=LeadDatePresetCallback(
                        preset="30d"
                    ).pack(),
                    style=ButtonStyle.PRIMARY,
                ),
                InlineKeyboardButton(
                    text="Свой период",
                    callback_data=LeadDatePresetCallback(
                        preset="custom"
                    ).pack(),
                    style=ButtonStyle.PRIMARY,
                ),
            ],
        ]
    )


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
                text="▶️ Взять в работу",
                callback_data=LeadStatusCallback(
                    lead_id=lead.id,
                    target_status=(
                        LeadStatus.IN_PROGRESS.value
                    ),
                    list_type=list_type,
                    page=page,
                ).pack(),
                style=ButtonStyle.SUCCESS,
            )
        )

    if lead.status == LeadStatus.CLOSED:
        builder.row(
            InlineKeyboardButton(
                text=REOPEN_LEAD_BUTTON,
                callback_data=LeadReopenCallback(
                    lead_id=lead.id,
                    list_type=list_type,
                    page=page,
                ).pack(),
                style=ButtonStyle.SUCCESS,
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
                style=ButtonStyle.DANGER,
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="💬 Связаться с клиентом",
            url=profile_url,
            style=ButtonStyle.PRIMARY,
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="← Назад к списку",
            callback_data=LeadPageCallback(
                list_type=list_type,
                page=page,
            ).pack(),
            style=ButtonStyle.PRIMARY,
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
                    style=ButtonStyle.DANGER,
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
                    text="✅ Подтвердить закрытие",
                    callback_data=(
                        LeadCloseDecisionCallback(
                            action="confirm",
                            lead_id=lead_id,
                            list_type=list_type,
                            page=page,
                        ).pack()
                    ),
                    style=ButtonStyle.DANGER,
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
                    style=ButtonStyle.PRIMARY,
                )
            ],
        ]
    )
