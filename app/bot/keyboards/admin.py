from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aiogram.enums import ButtonStyle
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.callbacks import (
    AdminInputCancelCallback,
    ClientLeadOpenCallback,
    ClientLeadPageCallback,
    ClientOpenCallback,
    ClientPageCallback,
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


if TYPE_CHECKING:
    from app.services.admin_lead_service import ClientSummary


ADMIN_PANEL_BUTTON = "⚙️ Админ-панель"
NEW_LEADS_BUTTON = "🆕 Новые заявки"
ACTIVE_LEADS_BUTTON = "📂 Активные заявки"
ARCHIVE_BUTTON = "🗄 Архив"
SEARCH_LEADS_BUTTON = "🔎 Найти заявку"
DATE_FILTER_BUTTON = "📅 Фильтр по датам"
CLIENTS_BUTTON = "👥 Клиенты"
REFRESH_PANEL_BUTTON = "🔄 Обновить статистику"
ENABLE_NOTIFICATIONS_BUTTON = "🔔 Включить уведомления"
DISABLE_NOTIFICATIONS_BUTTON = "🔕 Отключить уведомления"
USER_MODE_BUTTON = "👤 Пользовательский режим"
CLOSE_LEAD_BUTTON = "🔒 Закрыть заявку"
REOPEN_LEAD_BUTTON = "♻️ Вернуть в работу"
CANCEL_CLOSE_BUTTON = "↩️ Отменить закрытие"
CANCEL_INPUT_BUTTON = "↩️ Отменить ввод"


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
                    text=CLIENTS_BUTTON,
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


def get_admin_input_cancel_keyboard(
    *,
    action: str,
) -> InlineKeyboardMarkup:
    """Return a persistent inline cancellation action for text input."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=CANCEL_INPUT_BUTTON,
                    callback_data=AdminInputCancelCallback(
                        action=action,
                    ).pack(),
                    style=ButtonStyle.DANGER,
                )
            ]
        ]
    )


def get_client_list_keyboard(
    *,
    clients: Sequence["ClientSummary"],
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    """Return the paginated client-directory keyboard."""

    builder = InlineKeyboardBuilder()

    for client in clients:
        username = (
            f"@{client.username}"
            if client.username
            else str(client.telegram_user_id)
        )
        title = client.display_name[:22]

        builder.button(
            text=(
                f"👤 {title} · {username} · "
                f"{client.total_leads}"
            ),
            callback_data=ClientOpenCallback(
                client_id=client.client_id,
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
                callback_data=ClientPageCallback(
                    page=page - 1,
                ).pack(),
                style=ButtonStyle.PRIMARY,
            )
        )

    if page < total_pages:
        navigation.append(
            InlineKeyboardButton(
                text="Вперёд →",
                callback_data=ClientPageCallback(
                    page=page + 1,
                ).pack(),
                style=ButtonStyle.PRIMARY,
            )
        )

    if navigation:
        builder.row(*navigation)

    return builder.as_markup()


def get_client_card_keyboard(
    *,
    client: "ClientSummary",
    clients_page: int,
) -> InlineKeyboardMarkup:
    """Return actions available from a client card."""

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=f"📋 Заявки клиента · {client.total_leads}",
            callback_data=ClientLeadPageCallback(
                client_id=client.client_id,
                clients_page=clients_page,
                page=1,
            ).pack(),
            style=ButtonStyle.PRIMARY,
        )
    )

    profile_url = (
        f"https://t.me/{client.username}"
        if client.username
        else f"tg://user?id={client.telegram_user_id}"
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
            text="← Назад к клиентам",
            callback_data=ClientPageCallback(
                page=clients_page,
            ).pack(),
            style=ButtonStyle.PRIMARY,
        )
    )

    return builder.as_markup()


def get_client_lead_list_keyboard(
    *,
    leads: Sequence[Lead],
    client_id: int,
    clients_page: int,
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    """Return one client's paginated request keyboard."""

    builder = InlineKeyboardBuilder()

    for lead in leads:
        status_icon = STATUS_ICONS.get(lead.status, "•")

        builder.button(
            text=(
                f"{status_icon} №{lead.id} · "
                f"{lead.created_at:%d.%m.%Y}"
            ),
            callback_data=ClientLeadOpenCallback(
                lead_id=lead.id,
                clients_page=clients_page,
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
                callback_data=ClientLeadPageCallback(
                    client_id=client_id,
                    clients_page=clients_page,
                    page=page - 1,
                ).pack(),
                style=ButtonStyle.PRIMARY,
            )
        )

    if page < total_pages:
        navigation.append(
            InlineKeyboardButton(
                text="Вперёд →",
                callback_data=ClientLeadPageCallback(
                    client_id=client_id,
                    clients_page=clients_page,
                    page=page + 1,
                ).pack(),
                style=ButtonStyle.PRIMARY,
            )
        )

    if navigation:
        builder.row(*navigation)

    builder.row(
        InlineKeyboardButton(
            text="← К карточке клиента",
            callback_data=ClientOpenCallback(
                client_id=client_id,
                page=clients_page,
            ).pack(),
            style=ButtonStyle.PRIMARY,
        )
    )

    return builder.as_markup()


def get_lead_card_keyboard(
    *,
    lead: Lead,
    list_type: str,
    page: int,
    back_callback_data: str | None = None,
    back_text: str = "← Назад к списку",
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

    back_callback = (
        back_callback_data
        if back_callback_data is not None
        else LeadPageCallback(
            list_type=list_type,
            page=page,
        ).pack()
    )

    builder.row(
        InlineKeyboardButton(
            text=back_text,
            callback_data=back_callback,
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
