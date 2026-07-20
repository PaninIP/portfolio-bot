from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.callbacks import (
    LeadOpenCallback,
    LeadPageCallback,
)
from app.bot.filters import IsAdmin
from app.bot.keyboards.admin import (
    ACTIVE_LEADS_BUTTON,
    NEW_LEADS_BUTTON,
    get_lead_card_keyboard,
    get_lead_list_keyboard,
)
from app.database.enums import LeadStatus
from app.database.models.lead import Lead
from app.services.admin_lead_service import (
    LeadListType,
    LeadPage,
    get_admin_lead,
    get_lead_page,
)


router = Router(name=__name__)


STATUS_LABELS = {
    LeadStatus.NEW: "новая",
    LeadStatus.IN_PROGRESS: "в работе",
    LeadStatus.WAITING_FOR_CLIENT: "ожидает клиента",
    LeadStatus.CLOSED: "закрыта",
}


def build_lead_list_text(
    page: LeadPage,
) -> str:
    """Build the administrator lead-list heading."""

    title = (
        "Новые заявки"
        if page.list_type == LeadListType.NEW
        else "Активные заявки"
    )

    if page.total_items == 0:
        return (
            f"<b>{title}</b>\n\n"
            "Заявок в этом разделе пока нет."
        )

    return (
        f"<b>{title}</b>\n\n"
        f"Всего заявок: {page.total_items}\n"
        f"Страница: {page.page} из {page.total_pages}\n\n"
        "Выберите заявку:"
    )


def safe(value: object) -> str:
    """Return an HTML-safe value."""

    return escape(str(value))


def build_lead_card_text(lead: Lead) -> str:
    """Build a full administrator lead card."""

    user = lead.user
    username = (
        f"@{user.username}"
        if user.username
        else "не указан"
    )

    profile_name = " ".join(
        part
        for part in (
            user.first_name,
            user.last_name,
        )
        if part
    )

    status = STATUS_LABELS.get(
        lead.status,
        lead.status.value,
    )

    return (
        f"<b>Заявка №{lead.id}</b>\n\n"
        f"<b>Статус:</b> {safe(status)}\n"
        f"<b>Создана:</b> "
        f"{lead.created_at:%d.%m.%Y %H:%M}\n\n"
        f"<b>Имя для обращения:</b> "
        f"{safe(lead.contact_name)}\n"
        f"<b>Имя профиля:</b> "
        f"{safe(profile_name)}\n"
        f"<b>Username:</b> {safe(username)}\n"
        f"<b>Telegram ID:</b> "
        f"<code>{user.telegram_user_id}</code>\n"
        f"<b>Телефон:</b> "
        f"{safe(user.phone or 'не указан')}\n\n"
        f"<b>Описание проекта:</b>\n"
        f"{safe(lead.project_description)}\n\n"
        f"<b>Необходимые функции:</b>\n"
        f"{safe(lead.required_features)}\n\n"
        f"<b>Желаемый срок:</b> "
        f"{safe(lead.deadline)}\n"
        f"<b>Бюджет:</b> "
        f"{safe(lead.budget)}\n\n"
        f"<b>Комментарий:</b>\n"
        f"{safe(lead.client_comment or 'не указан')}"
    )


async def send_lead_page(
    message: Message,
    *,
    list_type: LeadListType,
    page_number: int,
    edit: bool = False,
) -> None:
    """Send or edit one administrator lead-list page."""

    page = await get_lead_page(
        list_type=list_type,
        page=page_number,
    )

    text = build_lead_list_text(page)
    keyboard = get_lead_list_keyboard(
        leads=page.items,
        list_type=page.list_type.value,
        page=page.page,
        total_pages=page.total_pages,
    )

    if edit:
        await message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@router.message(
    IsAdmin(),
    F.text == NEW_LEADS_BUTTON,
)
async def handle_new_leads(message: Message) -> None:
    """Show new project requests."""

    await send_lead_page(
        message,
        list_type=LeadListType.NEW,
        page_number=1,
    )


@router.message(
    IsAdmin(),
    F.text == ACTIVE_LEADS_BUTTON,
)
async def handle_active_leads(message: Message) -> None:
    """Show active project requests."""

    await send_lead_page(
        message,
        list_type=LeadListType.ACTIVE,
        page_number=1,
    )


@router.callback_query(
    IsAdmin(),
    LeadPageCallback.filter(),
)
async def handle_lead_page(
    callback: CallbackQuery,
    callback_data: LeadPageCallback,
) -> None:
    """Navigate to a lead-list page."""

    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    await send_lead_page(
        callback.message,
        list_type=LeadListType(
            callback_data.list_type
        ),
        page_number=callback_data.page,
        edit=True,
    )

    await callback.answer()


@router.callback_query(
    IsAdmin(),
    LeadOpenCallback.filter(),
)
async def handle_open_lead(
    callback: CallbackQuery,
    callback_data: LeadOpenCallback,
) -> None:
    """Open a full lead card."""

    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    lead = await get_admin_lead(
        callback_data.lead_id
    )

    if lead is None:
        await callback.answer(
            "Заявка не найдена.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        build_lead_card_text(lead),
        parse_mode="HTML",
        reply_markup=get_lead_card_keyboard(
            lead=lead,
            list_type=callback_data.list_type,
            page=callback_data.page,
        ),
    )

    await callback.answer()