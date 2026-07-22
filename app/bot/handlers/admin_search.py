import logging
import re
from datetime import date, datetime, timedelta, timezone
from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import SQLAlchemyError

from app.bot.callbacks import (
    AdminInputCancelCallback,
    LeadDatePresetCallback,
    LeadResultOpenCallback,
    LeadResultPageCallback,
)
from app.bot.filters import IsAdmin
from app.bot.handlers.admin_leads import build_lead_card_text
from app.bot.keyboards.admin import (
    DATE_FILTER_BUTTON,
    SEARCH_LEADS_BUTTON,
    get_admin_input_cancel_keyboard,
    get_date_filter_keyboard,
    get_lead_card_keyboard,
    get_lead_result_keyboard,
)
from app.bot.states.admin import (
    LeadDateFilterForm,
    LeadSearchForm,
)
from app.bot.views.admin_panel import show_admin_panel
from app.services.admin_lead_service import (
    LeadResultMode,
    LeadResultPage,
    get_admin_lead,
    get_date_result_page,
    get_lead_list_type,
    get_search_result_page,
)


router = Router(name=__name__)
logger = logging.getLogger(__name__)

CUSTOM_PERIOD_PATTERN = re.compile(
    r"^\s*(\d{2}\.\d{2}\.\d{4})\s*[-–—]\s*"
    r"(\d{2}\.\d{2}\.\d{4})\s*$"
)


def build_result_text(
    page: LeadResultPage,
    *,
    title: str,
) -> str:
    """Build a mixed-status result-list heading."""

    if page.total_items == 0:
        return (
            f"<b>{title}</b>\n\n"
            "Подходящих заявок не найдено."
        )

    return (
        f"<b>{title}</b>\n\n"
        f"Найдено заявок: {page.total_items}\n"
        f"Страница: {page.page} из {page.total_pages}\n\n"
        "Выберите заявку:"
    )


def parse_custom_period(value: str) -> tuple[date, date] | None:
    """Parse an inclusive DD.MM.YYYY-DD.MM.YYYY period."""

    match = CUSTOM_PERIOD_PATTERN.fullmatch(value)

    if match is None:
        return None

    try:
        start_date = datetime.strptime(
            match.group(1),
            "%d.%m.%Y",
        ).date()
        end_date = datetime.strptime(
            match.group(2),
            "%d.%m.%Y",
        ).date()
    except ValueError:
        return None

    if start_date > end_date:
        return None

    return start_date, end_date


def get_preset_period(preset: str) -> tuple[date, date] | None:
    """Return an inclusive UTC calendar period for a preset."""

    today = datetime.now(timezone.utc).date()

    if preset == "today":
        return today, today

    if preset == "7d":
        return today - timedelta(days=6), today

    if preset == "30d":
        return today - timedelta(days=29), today

    return None


async def get_stored_result_page(
    *,
    state: FSMContext,
    mode: LeadResultMode,
    page_number: int,
) -> tuple[LeadResultPage, str] | None:
    """Load one result page from criteria stored in FSM data."""

    data = await state.get_data()

    if data.get("result_mode") != mode.value:
        return None

    if mode == LeadResultMode.SEARCH:
        query = str(data.get("search_query", "")).strip()

        if not query:
            return None

        page = await get_search_result_page(
            query=query,
            page=page_number,
        )
        title = f"Результаты поиска: {escape(query)}"
        return page, title

    start_value = data.get("date_start")
    end_value = data.get("date_end")

    if not isinstance(start_value, str) or not isinstance(
        end_value,
        str,
    ):
        return None

    try:
        start_date = date.fromisoformat(start_value)
        end_date = date.fromisoformat(end_value)
    except ValueError:
        return None

    page = await get_date_result_page(
        start_date=start_date,
        end_date=end_date,
        page=page_number,
    )
    title = (
        "Заявки за период: "
        f"{start_date:%d.%m.%Y}–{end_date:%d.%m.%Y}"
    )

    return page, title


async def send_result_page(
    message: Message,
    *,
    state: FSMContext,
    mode: LeadResultMode,
    page_number: int,
    edit: bool = False,
) -> bool:
    """Send or edit one stored search/date-filter result page."""

    try:
        result = await get_stored_result_page(
            state=state,
            mode=mode,
            page_number=page_number,
        )
    except SQLAlchemyError:
        logger.exception(
            "Failed to load %s result page",
            mode.value,
        )
        return False

    if result is None:
        return False

    page, title = result
    text = build_result_text(page, title=title)
    keyboard = get_lead_result_keyboard(
        leads=page.items,
        mode=mode.value,
        page=page.page,
        total_pages=page.total_pages,
    )

    if edit:
        await message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    else:
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )

    return True


@router.callback_query(
    IsAdmin(),
    AdminInputCancelCallback.filter(),
)
async def handle_cancel_admin_input(
    callback: CallbackQuery,
    callback_data: AdminInputCancelCallback,
    state: FSMContext,
) -> None:
    """Cancel search or custom-period input and restore the panel."""

    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    await state.clear()

    await callback.message.answer(
        "Ввод отменён."
    )
    await show_admin_panel(callback.message)

    await callback.answer()


@router.message(
    IsAdmin(),
    F.text == SEARCH_LEADS_BUTTON,
)
async def handle_start_search(
    message: Message,
    state: FSMContext,
) -> None:
    """Request a general administrator search query."""

    await state.clear()
    await state.set_state(LeadSearchForm.query)

    await message.answer(
        "Введите одно из значений:\n\n"
        "• номер заявки;\n"
        "• имя клиента;\n"
        "• @username;\n"
        "• Telegram ID;\n"
        "• телефон.\n\n"
        "Нажмите кнопку ниже, чтобы отменить ввод.",
        reply_markup=get_admin_input_cancel_keyboard(
            action="search",
        ),
    )


@router.message(
    IsAdmin(),
    LeadSearchForm.query,
)
async def handle_search_query(
    message: Message,
    state: FSMContext,
) -> None:
    """Search leads using the administrator's text query."""

    query = message.text.strip() if message.text else ""

    if len(query) < 2 and not query.isdigit():
        await message.answer(
            "Введите минимум два символа или полный номер заявки."
        )
        return

    await state.update_data(
        result_mode=LeadResultMode.SEARCH.value,
        search_query=query,
    )
    await state.set_state(LeadSearchForm.results)

    sent = await send_result_page(
        message,
        state=state,
        mode=LeadResultMode.SEARCH,
        page_number=1,
    )

    if not sent:
        await message.answer(
            "Не удалось выполнить поиск. Попробуйте ещё раз."
        )


@router.message(
    IsAdmin(),
    F.text == DATE_FILTER_BUTTON,
)
async def handle_start_date_filter(
    message: Message,
    state: FSMContext,
) -> None:
    """Show available creation-date filters."""

    await state.clear()

    await message.answer(
        "Выберите период создания заявок.\n\n"
        "Дата рассчитывается по UTC.",
        reply_markup=get_date_filter_keyboard(),
    )


@router.callback_query(
    IsAdmin(),
    LeadDatePresetCallback.filter(),
)
async def handle_date_preset(
    callback: CallbackQuery,
    callback_data: LeadDatePresetCallback,
    state: FSMContext,
) -> None:
    """Apply a predefined period or request a custom one."""

    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    if callback_data.preset == "custom":
        await state.clear()
        await state.set_state(
            LeadDateFilterForm.custom_period
        )

        await callback.message.answer(
            "Введите период в формате:\n"
            "01.07.2026-31.07.2026",
            reply_markup=get_admin_input_cancel_keyboard(
                action="date",
            ),
        )
        await callback.answer()
        return

    period = get_preset_period(callback_data.preset)

    if period is None:
        await callback.answer(
            "Неизвестный период.",
            show_alert=True,
        )
        return

    start_date, end_date = period

    await state.clear()
    await state.update_data(
        result_mode=LeadResultMode.DATE.value,
        date_start=start_date.isoformat(),
        date_end=end_date.isoformat(),
    )
    await state.set_state(LeadDateFilterForm.results)

    sent = await send_result_page(
        callback.message,
        state=state,
        mode=LeadResultMode.DATE,
        page_number=1,
    )

    if sent:
        await callback.answer()
    else:
        await callback.answer(
            "Не удалось применить фильтр.",
            show_alert=True,
        )


@router.message(
    IsAdmin(),
    LeadDateFilterForm.custom_period,
)
async def handle_custom_date_period(
    message: Message,
    state: FSMContext,
) -> None:
    """Parse and apply a custom inclusive date period."""

    value = message.text.strip() if message.text else ""
    period = parse_custom_period(value)

    if period is None:
        await message.answer(
            "Некорректный период. Используйте формат:\n"
            "01.07.2026-31.07.2026\n\n"
            "Начальная дата не должна быть позже конечной."
        )
        return

    start_date, end_date = period

    await state.update_data(
        result_mode=LeadResultMode.DATE.value,
        date_start=start_date.isoformat(),
        date_end=end_date.isoformat(),
    )
    await state.set_state(LeadDateFilterForm.results)

    sent = await send_result_page(
        message,
        state=state,
        mode=LeadResultMode.DATE,
        page_number=1,
    )

    if not sent:
        await message.answer(
            "Не удалось применить фильтр. Попробуйте ещё раз."
        )


@router.callback_query(
    IsAdmin(),
    LeadResultPageCallback.filter(),
)
async def handle_result_page(
    callback: CallbackQuery,
    callback_data: LeadResultPageCallback,
    state: FSMContext,
) -> None:
    """Navigate paginated search or date-filter results."""

    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    try:
        mode = LeadResultMode(callback_data.mode)
    except ValueError:
        await callback.answer(
            "Неизвестный тип результатов.",
            show_alert=True,
        )
        return

    sent = await send_result_page(
        callback.message,
        state=state,
        mode=mode,
        page_number=callback_data.page,
        edit=True,
    )

    if sent:
        await callback.answer()
    else:
        await callback.answer(
            "Результаты устарели. Запустите поиск заново.",
            show_alert=True,
        )


@router.callback_query(
    IsAdmin(),
    LeadResultOpenCallback.filter(),
)
async def handle_open_result_lead(
    callback: CallbackQuery,
    callback_data: LeadResultOpenCallback,
) -> None:
    """Open a result card in a new message."""

    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    try:
        lead = await get_admin_lead(
            callback_data.lead_id
        )
    except SQLAlchemyError:
        logger.exception(
            "Failed to open result lead %s",
            callback_data.lead_id,
        )
        lead = None

    if lead is None:
        await callback.answer(
            "Заявка не найдена.",
            show_alert=True,
        )
        return

    list_type = get_lead_list_type(lead.status)

    await callback.message.answer(
        build_lead_card_text(lead),
        parse_mode="HTML",
        reply_markup=get_lead_card_keyboard(
            lead=lead,
            list_type=list_type.value,
            page=1,
        ),
    )

    await callback.answer()
