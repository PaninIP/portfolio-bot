import logging
from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import SQLAlchemyError

from app.bot.callbacks import (
    ClientLeadOpenCallback,
    ClientLeadPageCallback,
    ClientOpenCallback,
    ClientPageCallback,
)
from app.bot.filters import IsAdmin
from app.bot.handlers.admin_leads import build_lead_card_text
from app.bot.keyboards.admin import (
    CLIENTS_BUTTON,
    get_client_card_keyboard,
    get_client_lead_list_keyboard,
    get_client_list_keyboard,
    get_lead_card_keyboard,
)
from app.services.admin_lead_service import (
    ClientLeadPage,
    ClientPage,
    ClientSummary,
    get_admin_lead,
    get_client_lead_page,
    get_client_page,
    get_client_summary,
    get_lead_list_type,
)


router = Router(name=__name__)
logger = logging.getLogger(__name__)


def safe(value: object) -> str:
    """Return an HTML-safe value."""

    return escape(str(value))


def build_client_list_text(page: ClientPage) -> str:
    """Build the administrator client-directory heading."""

    if page.total_items == 0:
        return (
            "<b>Клиенты</b>\n\n"
            "Пользователей с заявками пока нет."
        )

    return (
        "<b>Клиенты</b>\n\n"
        f"Всего клиентов: {page.total_items}\n"
        f"Страница: {page.page} из {page.total_pages}\n\n"
        "Выберите клиента:"
    )


def build_client_card_text(client: ClientSummary) -> str:
    """Build a full administrator client card."""

    username = (
        f"@{client.username}"
        if client.username
        else "не указан"
    )

    return (
        "<b>Карточка клиента</b>\n\n"
        f"<b>Имя профиля:</b> "
        f"{safe(client.display_name)}\n"
        f"<b>Username:</b> {safe(username)}\n"
        f"<b>Telegram ID:</b> "
        f"<code>{client.telegram_user_id}</code>\n"
        f"<b>Телефон:</b> "
        f"{safe(client.phone or 'не указан')}\n\n"
        f"<b>Всего заявок:</b> {client.total_leads}\n"
        f"<b>Открытых:</b> {client.open_leads}\n"
        f"<b>Закрытых:</b> {client.closed_leads}\n"
        f"<b>Последняя заявка:</b> "
        f"{client.last_lead_at:%d.%m.%Y %H:%M}"
    )


def build_client_lead_list_text(
    page: ClientLeadPage,
    client: ClientSummary,
) -> str:
    """Build the request-list heading for one client."""

    return (
        f"<b>Заявки клиента: "
        f"{safe(client.display_name)}</b>\n\n"
        f"Всего заявок: {page.total_items}\n"
        f"Страница: {page.page} из {page.total_pages}\n\n"
        "Выберите заявку:"
    )


async def send_client_page(
    message: Message,
    *,
    page_number: int,
    edit: bool = False,
) -> None:
    """Send or edit one page of the client directory."""

    page = await get_client_page(page=page_number)
    text = build_client_list_text(page)
    keyboard = get_client_list_keyboard(
        clients=page.items,
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


async def send_client_lead_page(
    message: Message,
    *,
    client_id: int,
    clients_page: int,
    page_number: int,
) -> bool:
    """Edit a message with one client's paginated requests."""

    client = await get_client_summary(client_id)

    if client is None:
        return False

    page = await get_client_lead_page(
        client_id=client_id,
        page=page_number,
    )

    await message.edit_text(
        build_client_lead_list_text(page, client),
        parse_mode="HTML",
        reply_markup=get_client_lead_list_keyboard(
            leads=page.items,
            client_id=client_id,
            clients_page=clients_page,
            page=page.page,
            total_pages=page.total_pages,
        ),
    )

    return True


@router.message(
    IsAdmin(),
    F.text == CLIENTS_BUTTON,
)
async def handle_clients(
    message: Message,
    state: FSMContext,
) -> None:
    """Show clients who submitted at least one request."""

    await state.clear()

    try:
        await send_client_page(
            message,
            page_number=1,
        )
    except SQLAlchemyError:
        logger.exception("Failed to load client directory")
        await message.answer(
            "Не удалось загрузить список клиентов."
        )


@router.callback_query(
    IsAdmin(),
    ClientPageCallback.filter(),
)
async def handle_client_page(
    callback: CallbackQuery,
    callback_data: ClientPageCallback,
) -> None:
    """Navigate client-directory pages."""

    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    try:
        await send_client_page(
            callback.message,
            page_number=callback_data.page,
            edit=True,
        )
    except SQLAlchemyError:
        logger.exception("Failed to load client page")
        await callback.answer(
            "Не удалось загрузить клиентов.",
            show_alert=True,
        )
        return

    await callback.answer()


@router.callback_query(
    IsAdmin(),
    ClientOpenCallback.filter(),
)
async def handle_open_client(
    callback: CallbackQuery,
    callback_data: ClientOpenCallback,
) -> None:
    """Open a full client card."""

    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    try:
        client = await get_client_summary(
            callback_data.client_id
        )
    except SQLAlchemyError:
        logger.exception(
            "Failed to load client %s",
            callback_data.client_id,
        )
        client = None

    if client is None:
        await callback.answer(
            "Клиент не найден.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        build_client_card_text(client),
        parse_mode="HTML",
        reply_markup=get_client_card_keyboard(
            client=client,
            clients_page=callback_data.page,
        ),
    )

    await callback.answer()


@router.callback_query(
    IsAdmin(),
    ClientLeadPageCallback.filter(),
)
async def handle_client_lead_page(
    callback: CallbackQuery,
    callback_data: ClientLeadPageCallback,
) -> None:
    """Navigate one client's requests."""

    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    try:
        sent = await send_client_lead_page(
            callback.message,
            client_id=callback_data.client_id,
            clients_page=callback_data.clients_page,
            page_number=callback_data.page,
        )
    except SQLAlchemyError:
        logger.exception(
            "Failed to load leads for client %s",
            callback_data.client_id,
        )
        sent = False

    if not sent:
        await callback.answer(
            "Клиент или его заявки не найдены.",
            show_alert=True,
        )
        return

    await callback.answer()


@router.callback_query(
    IsAdmin(),
    ClientLeadOpenCallback.filter(),
)
async def handle_open_client_lead(
    callback: CallbackQuery,
    callback_data: ClientLeadOpenCallback,
) -> None:
    """Open a request selected from a client card."""

    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    try:
        lead = await get_admin_lead(
            callback_data.lead_id
        )
    except SQLAlchemyError:
        logger.exception(
            "Failed to load client lead %s",
            callback_data.lead_id,
        )
        lead = None

    if lead is None:
        await callback.answer(
            "Заявка не найдена.",
            show_alert=True,
        )
        return

    client_id = lead.user_id
    list_type = get_lead_list_type(lead.status)
    back_callback = ClientLeadPageCallback(
        client_id=client_id,
        clients_page=callback_data.clients_page,
        page=callback_data.page,
    ).pack()

    await callback.message.edit_text(
        build_lead_card_text(lead),
        parse_mode="HTML",
        reply_markup=get_lead_card_keyboard(
            lead=lead,
            list_type=list_type.value,
            page=1,
            back_callback_data=back_callback,
            back_text="← К заявкам клиента",
        ),
    )

    await callback.answer()
