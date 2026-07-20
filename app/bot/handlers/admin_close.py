import logging
from html import escape

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Message,
    ReplyKeyboardRemove,
)
from sqlalchemy.exc import SQLAlchemyError

from app.bot.callbacks import (
    LeadCloseCallback,
    LeadCloseDecisionCallback,
)
from app.bot.filters import IsAdmin
from app.bot.keyboards.admin import (
    CANCEL_CLOSE_BUTTON,
    get_admin_keyboard,
    get_close_comment_keyboard,
    get_close_confirmation_keyboard,
)
from app.bot.states.admin import LeadCloseForm
from app.database.enums import LeadStatus
from app.services.admin_lead_service import (
    get_admin_lead,
)
from app.services.admin_service import (
    get_admin_panel_data,
)
from app.services.lead_closing_service import (
    close_lead,
    record_close_notification_delivery,
)
from app.services.lead_notification import (
    send_lead_closed_to_client,
)


router = Router(name=__name__)
logger = logging.getLogger(__name__)


async def restore_admin_keyboard(
    message: Message,
) -> None:
    """Restore the administrator reply keyboard."""

    user = message.from_user

    if user is None:
        return

    data = await get_admin_panel_data(user.id)

    await message.answer(
        "Выберите следующий раздел.",
        reply_markup=get_admin_keyboard(
            notifications_enabled=(
                data.notifications_enabled
            ),
        ),
    )


@router.callback_query(
    IsAdmin(),
    LeadCloseCallback.filter(),
)
async def handle_start_lead_close(
    callback: CallbackQuery,
    callback_data: LeadCloseCallback,
    state: FSMContext,
) -> None:
    """Request a mandatory closing comment."""

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

    if lead.status == LeadStatus.CLOSED:
        await callback.answer(
            "Заявка уже закрыта.",
            show_alert=True,
        )
        return

    await state.clear()
    await state.update_data(
        lead_id=lead.id,
        list_type=callback_data.list_type,
        page=callback_data.page,
        card_chat_id=callback.message.chat.id,
        card_message_id=callback.message.message_id,
    )
    await state.set_state(LeadCloseForm.comment)

    await callback.message.answer(
        f"Введите комментарий для закрытия "
        f"заявки №{lead.id}.\n\n"
        "Комментарий будет отправлен клиенту.",
        reply_markup=get_close_comment_keyboard(),
    )

    await callback.answer()


@router.message(
    IsAdmin(),
    LeadCloseForm.comment,
    F.text == CANCEL_CLOSE_BUTTON,
)
async def handle_cancel_close_by_text(
    message: Message,
    state: FSMContext,
) -> None:
    """Cancel closing before confirmation."""

    await state.clear()

    await message.answer(
        "Закрытие заявки отменено.",
        reply_markup=ReplyKeyboardRemove(),
    )

    await restore_admin_keyboard(message)


@router.message(
    IsAdmin(),
    LeadCloseForm.comment,
)
async def handle_close_comment(
    message: Message,
    state: FSMContext,
) -> None:
    """Save a closing comment and request confirmation."""

    comment = (
        message.text.strip()
        if message.text
        else ""
    )

    if len(comment) < 3:
        await message.answer(
            "Комментарий должен содержать "
            "минимум три символа."
        )
        return

    data = await state.get_data()
    lead_id = int(data["lead_id"])
    list_type = str(data["list_type"])
    page = int(data["page"])

    await state.update_data(close_comment=comment)
    await state.set_state(
        LeadCloseForm.confirmation
    )

    await message.answer(
        "Комментарий сохранён.",
        reply_markup=ReplyKeyboardRemove(),
    )

    await message.answer(
        f"<b>Закрыть заявку №{lead_id}?</b>\n\n"
        f"<b>Комментарий клиенту:</b>\n"
        f"{escape(comment)}",
        parse_mode="HTML",
        reply_markup=get_close_confirmation_keyboard(
            lead_id=lead_id,
            list_type=list_type,
            page=page,
        ),
    )


@router.callback_query(
    IsAdmin(),
    LeadCloseDecisionCallback.filter(
        F.action == "cancel"
    ),
)
async def handle_cancel_close(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Cancel a confirmed closing operation."""

    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    await state.clear()

    await callback.message.edit_text(
        "Закрытие заявки отменено."
    )

    await restore_admin_keyboard(
        callback.message
    )
    await callback.answer()


@router.callback_query(
    IsAdmin(),
    LeadCloseDecisionCallback.filter(
        F.action == "confirm"
    ),
)
async def handle_confirm_close(
    callback: CallbackQuery,
    callback_data: LeadCloseDecisionCallback,
    state: FSMContext,
) -> None:
    """Close a lead and notify its client."""

    if not isinstance(callback.message, Message):
        await callback.answer()
        return

    user = callback.from_user
    data = await state.get_data()

    if int(data.get("lead_id", 0)) != callback_data.lead_id:
        await callback.answer(
            "Данные операции устарели.",
            show_alert=True,
        )
        return

    comment = str(data.get("close_comment", "")).strip()

    try:
        result = await close_lead(
            lead_id=callback_data.lead_id,
            admin_telegram_id=user.id,
            comment=comment,
        )
    except SQLAlchemyError:
        logger.exception(
            "Failed to close lead %s",
            callback_data.lead_id,
        )

        await callback.answer(
            "Не удалось закрыть заявку.",
            show_alert=True,
        )
        return

    if not result.found:
        await state.clear()
        await callback.answer(
            "Заявка не найдена.",
            show_alert=True,
        )
        return

    if not result.changed:
        await state.clear()
        await callback.answer(
            "Статус заявки уже изменён.",
            show_alert=True,
        )
        return

    await state.clear()

    delivered = False
    delivery_error: str | None = None

    try:
        await send_lead_closed_to_client(
            bot=callback.bot,
            client_telegram_id=(
                result.client_telegram_id
            ),
            lead_id=result.lead_id,
            comment=result.close_comment or comment,
        )
        delivered = True
    except TelegramAPIError as error:
        delivery_error = str(error)

        logger.exception(
            "Lead %s closed, but client notification failed",
            result.lead_id,
        )

    if (
        result.lead_id is not None
        and result.admin_comment_id is not None
        and result.client_telegram_id is not None
    ):
        try:
            await record_close_notification_delivery(
                lead_id=result.lead_id,
                admin_comment_id=(
                    result.admin_comment_id
                ),
                recipient_telegram_id=(
                    result.client_telegram_id
                ),
                delivered=delivered,
                error_message=delivery_error,
            )
        except SQLAlchemyError:
            logger.exception(
                "Failed to record notification for lead %s",
                result.lead_id,
            )

    card_chat_id = data.get("card_chat_id")
    card_message_id = data.get("card_message_id")

    if card_chat_id and card_message_id:
        try:
            await callback.bot.delete_message(
                chat_id=int(card_chat_id),
                message_id=int(card_message_id),
            )
        except TelegramAPIError:
            logger.debug(
                "Could not delete the previous lead card"
            )

    delivery_text = (
        "Клиент уведомлён."
        if delivered
        else "Не удалось уведомить клиента."
    )

    await callback.message.edit_text(
        f"<b>Заявка №{result.lead_id} закрыта.</b>\n\n"
        f"{delivery_text}\n"
        "Заявка перемещена в архив.",
        parse_mode="HTML",
    )

    await restore_admin_keyboard(
        callback.message
    )

    await callback.answer(
        "Заявка закрыта."
    )