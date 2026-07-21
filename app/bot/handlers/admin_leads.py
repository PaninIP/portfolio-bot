import logging
from html import escape

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import SQLAlchemyError

from app.bot.callbacks import (
    LeadOpenCallback,
    LeadPageCallback,
    LeadReopenCallback,
    LeadStatusCallback,
)
from app.bot.filters import IsAdmin
from app.bot.keyboards.admin import (
    ACTIVE_LEADS_BUTTON,
    ARCHIVE_BUTTON,
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
    record_reopen_notification_delivery,
    reopen_closed_lead,
    take_lead_in_progress,
)


router = Router(name=__name__)
logger = logging.getLogger(__name__)


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

    titles = {
        LeadListType.NEW: "Новые заявки",
        LeadListType.ACTIVE: "Активные заявки",
        LeadListType.ARCHIVE: "Архив",
    }

    title = titles[page.list_type]

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
    ) or "не указано"

    status = STATUS_LABELS.get(
        lead.status,
        lead.status.value,
    )

    closed_section = ""

    if lead.status == LeadStatus.CLOSED:
        closed_at_text = (
            lead.closed_at.strftime(
                "%d.%m.%Y %H:%M"
            )
            if lead.closed_at
            else "не указана"
        )

        closed_section = (
            "\n\n<b>Закрытие заявки:</b>\n"
            f"<b>Дата:</b> {closed_at_text}\n"
            f"<b>Комментарий:</b> "
            f"{safe(lead.close_comment or 'не указан')}"
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
        f"<b>Комментарий клиента:</b>\n"
        f"{safe(lead.client_comment or 'не указан')}"
        f"{closed_section}"
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


@router.message(
    IsAdmin(),
    F.text == ARCHIVE_BUTTON,
)
async def handle_archive(message: Message) -> None:
    """Show closed project requests."""

    await send_lead_page(
        message,
        list_type=LeadListType.ARCHIVE,
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


@router.callback_query(
    IsAdmin(),
    LeadStatusCallback.filter(
        F.target_status
        == LeadStatus.IN_PROGRESS.value
    ),
)
async def handle_take_lead_in_progress(
    callback: CallbackQuery,
    callback_data: LeadStatusCallback,
) -> None:
    """Move a new lead into active work."""

    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    result = await take_lead_in_progress(
        lead_id=callback_data.lead_id,
        admin_telegram_id=callback.from_user.id,
    )

    if not result.found:
        await callback.answer(
            "Заявка не найдена.",
            show_alert=True,
        )
        return

    if not result.changed:
        status_label = STATUS_LABELS.get(
            result.current_status,
            "неизвестный статус",
        )

        await callback.answer(
            f"Статус заявки уже изменён: "
            f"{status_label}.",
            show_alert=True,
        )
        return

    lead = await get_admin_lead(
        callback_data.lead_id
    )

    if lead is None:
        await callback.answer(
            "Не удалось обновить карточку заявки.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        build_lead_card_text(lead),
        parse_mode="HTML",
        reply_markup=get_lead_card_keyboard(
            lead=lead,
            list_type=LeadListType.ACTIVE.value,
            page=1,
        ),
    )

    await callback.answer(
        "Заявка взята в работу."
    )


@router.callback_query(
    IsAdmin(),
    LeadReopenCallback.filter(),
)
async def handle_reopen_lead(
    callback: CallbackQuery,
    callback_data: LeadReopenCallback,
) -> None:
    """Return a closed lead to active work."""

    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    try:
        result = await reopen_closed_lead(
            lead_id=callback_data.lead_id,
            admin_telegram_id=callback.from_user.id,
        )
    except SQLAlchemyError:
        logger.exception(
            "Failed to reopen lead %s",
            callback_data.lead_id,
        )

        await callback.answer(
            "Не удалось вернуть заявку в работу.",
            show_alert=True,
        )
        return

    if not result.found:
        await callback.answer(
            "Заявка не найдена.",
            show_alert=True,
        )
        return

    if not result.changed:
        status_label = STATUS_LABELS.get(
            result.current_status,
            "неизвестный статус",
        )

        await callback.answer(
            f"Заявка уже имеет статус: {status_label}.",
            show_alert=True,
        )
        return

    delivered = False
    delivery_error: str | None = None

    if (
        result.client_telegram_id is not None
        and result.lead_id is not None
    ):
        try:
            await callback.bot.send_message(
                chat_id=result.client_telegram_id,
                text=(
                    f"Заявка №{result.lead_id} снова "
                    "передана в работу.\n\n"
                    "Panini продолжит работу "
                    "с вашим обращением."
                ),
            )
            delivered = True
        except TelegramAPIError as error:
            delivery_error = str(error)

            logger.exception(
                "Lead %s reopened, but client notification failed",
                result.lead_id,
            )

        try:
            await record_reopen_notification_delivery(
                lead_id=result.lead_id,
                recipient_telegram_id=(
                    result.client_telegram_id
                ),
                delivered=delivered,
                error_message=delivery_error,
            )
        except SQLAlchemyError:
            logger.exception(
                "Failed to record reopening notification "
                "for lead %s",
                result.lead_id,
            )

    try:
        lead = await get_admin_lead(
            callback_data.lead_id
        )
    except SQLAlchemyError:
        logger.exception(
            "Failed to reload reopened lead %s",
            callback_data.lead_id,
        )
        lead = None

    if lead is None:
        await callback.answer(
            "Заявка возвращена в работу, "
            "но карточку обновить не удалось.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        build_lead_card_text(lead),
        parse_mode="HTML",
        reply_markup=get_lead_card_keyboard(
            lead=lead,
            list_type=LeadListType.ACTIVE.value,
            page=1,
        ),
    )

    if delivered:
        await callback.answer(
            "Заявка возвращена в работу."
        )
    else:
        await callback.answer(
            "Заявка возвращена в работу, "
            "но клиент не уведомлён.",
            show_alert=True,
        )
