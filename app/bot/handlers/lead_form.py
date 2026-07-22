import logging

from sqlalchemy.exc import SQLAlchemyError

from app.services.lead_service import LeadSubmission, create_lead

from html import escape
from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from aiogram.exceptions import TelegramAPIError

from app.config import get_settings
from app.database.enums import AttachmentType
from app.services.lead_notification import send_lead_to_admin

from app.services.admin_service import (
    admin_notifications_enabled,
    is_configured_admin,
)

from app.bot.filters import IsAdmin
from app.bot.views.admin_panel import show_admin_panel
from app.bot.keyboards.admin import ADMIN_PANEL_BUTTON
from app.bot.keyboards.lead_form import (
    CANCEL_BUTTON,
    CONFIRM_BUTTON,
    DONE_ATTACHMENTS_BUTTON,
    ENTER_CUSTOM_NAME_BUTTON,
    RESTART_BUTTON,
    SKIP_ATTACHMENTS_BUTTON,
    SKIP_BUTTON,
    USE_PROFILE_NAME_BUTTON,
    get_attachments_keyboard,
    get_cancel_keyboard,
    get_comment_keyboard,
    get_confirmation_keyboard,
    get_contact_keyboard,
    get_name_choice_keyboard,
)
from app.bot.keyboards.main_menu import (
    DISCUSS_PROJECT_BUTTON,
    get_main_menu_keyboard,
)
from app.bot.states.lead_form import LeadForm


router = Router(name=__name__)

logger = logging.getLogger(__name__)

MAX_ATTACHMENTS = 10


def should_show_admin_panel(message: Message) -> bool:
    """Return whether the administrator shortcut should be shown."""

    user = message.from_user

    return bool(
        user
        and is_configured_admin(user.id)
    )


def get_message_text(message: Message) -> str | None:
    """Return stripped message text or None."""

    if message.text is None:
        return None

    text = message.text.strip()

    return text or None


def get_profile_name(message: Message) -> str:
    """Return the user's full name from the Telegram profile."""

    user = message.from_user

    if user is None:
        return "Пользователь Telegram"

    profile_name = " ".join(
        part
        for part in (
            user.first_name,
            user.last_name,
        )
        if part
    ).strip()

    return profile_name or "Пользователь Telegram"


def format_html(value: object) -> str:
    """Convert a value into an HTML-safe string."""

    return escape(str(value))


def get_attachment_data(
    message: Message,
) -> dict[str, Any] | None:
    """Extract supported Telegram attachment metadata."""

    caption = (message.caption or "").strip() or None

    if message.document is not None:
        file = message.document
        attachment_type = AttachmentType.DOCUMENT
        file_name = file.file_name
        mime_type = file.mime_type
    elif message.photo:
        file = message.photo[-1]
        attachment_type = AttachmentType.PHOTO
        file_name = None
        mime_type = "image/jpeg"
    elif message.video is not None:
        file = message.video
        attachment_type = AttachmentType.VIDEO
        file_name = file.file_name
        mime_type = file.mime_type
    elif message.audio is not None:
        file = message.audio
        attachment_type = AttachmentType.AUDIO
        file_name = file.file_name
        mime_type = file.mime_type
    elif message.voice is not None:
        file = message.voice
        attachment_type = AttachmentType.VOICE
        file_name = None
        mime_type = file.mime_type
    else:
        return None

    return {
        "attachment_type": attachment_type.value,
        "telegram_file_id": file.file_id,
        "telegram_file_unique_id": file.file_unique_id,
        "file_name": (file_name[:255] if file_name else None),
        "mime_type": (mime_type[:255] if mime_type else None),
        "file_size": file.file_size,
        "caption": caption,
    }


def get_attachment_label(data: dict[str, Any]) -> str:
    """Return a user-facing attachment label."""

    file_name = data.get("file_name")

    if file_name:
        return str(file_name)

    labels = {
        AttachmentType.PHOTO.value: "фотография",
        AttachmentType.VIDEO.value: "видео",
        AttachmentType.AUDIO.value: "аудиофайл",
        AttachmentType.VOICE.value: "голосовое сообщение",
        AttachmentType.DOCUMENT.value: "документ",
    }

    return labels.get(
        str(data.get("attachment_type")),
        "вложение",
    )


def build_lead_summary(data: dict[str, Any]) -> str:
    """Build a readable project request summary."""

    username = data.get("telegram_username")
    username_text = f"@{username}" if username else "не указан"

    contact_name = " ".join(
        part
        for part in (
            data.get("contact_first_name"),
            data.get("contact_last_name"),
        )
        if part
    ).strip()

    return (
        "<b>Предварительное техническое задание</b>\n\n"
        f"<b>Имя для обращения:</b> "
        f"{format_html(data.get('name', 'не указано'))}\n\n"
        "<b>Контакт Telegram:</b>\n"
        f"Имя профиля: "
        f"{format_html(contact_name or 'не указано')}\n"
        f"Username: {format_html(username_text)}\n"
        f"Telegram ID: "
        f"<code>{format_html(data.get('telegram_user_id', 'не указан'))}</code>\n"
        f"Телефон: "
        f"{format_html(data.get('contact_phone', 'не указан'))}\n\n"
        "<b>Описание проекта:</b>\n"
        f"{format_html(data.get('project_description', 'не указано'))}\n\n"
        "<b>Необходимые функции:</b>\n"
        f"{format_html(data.get('required_features', 'не указаны'))}\n\n"
        f"<b>Желаемый срок:</b> "
        f"{format_html(data.get('deadline', 'не указан'))}\n"
        f"<b>Ориентировочный бюджет:</b> "
        f"{format_html(data.get('budget', 'не указан'))}\n\n"
        "<b>Комментарий:</b>\n"
        f"{format_html(data.get('comment', 'не указан'))}\n\n"
        f"<b>Вложения:</b> "
        f"{len(data.get('attachments') or [])}"
    )


async def ask_for_contact(
    message: Message,
    state: FSMContext,
) -> None:
    """Request the client's Telegram contact."""

    await state.set_state(LeadForm.contact)

    await message.answer(
        "Передайте контакт Telegram, чтобы Panini мог связаться с вами.\n\n"
        "Telegram запросит подтверждение перед отправкой номера.",
        reply_markup=get_contact_keyboard(
            show_admin_panel=should_show_admin_panel(message),
        ),
    )


async def start_lead_form(
    message: Message,
    state: FSMContext,
) -> None:
    """Start collecting a project request."""

    await state.clear()

    profile_name = get_profile_name(message)

    await state.update_data(profile_name=profile_name)
    await state.set_state(LeadForm.name_choice)

    await message.answer(
        "Начнём заполнение заявки.\n\n"
        f"В вашем Telegram-профиле указано имя: "
        f"{profile_name}\n\n"
        "Использовать его для обращения или указать другое?",
        reply_markup=get_name_choice_keyboard(
            show_admin_panel=should_show_admin_panel(message),
        ),
    )


async def ask_for_attachments(
    message: Message,
    state: FSMContext,
) -> None:
    """Start the optional attachment-collection step."""

    data = await state.get_data()

    if "attachments" not in data:
        await state.update_data(attachments=[])

    await state.set_state(LeadForm.attachments)

    await message.answer(
        "📎 Прикрепите материалы к проекту.\n\n"
        "Можно отправить документы, фотографии, видео, "
        "аудио или голосовые сообщения — до 10 файлов.\n\n"
        "Когда закончите, нажмите «Готово». "
        "Если материалов нет — «Без вложений».",
        reply_markup=get_attachments_keyboard(
            show_admin_panel=should_show_admin_panel(message),
        ),
    )


async def show_confirmation(
    message: Message,
    state: FSMContext,
) -> None:
    """Show the collected request before confirmation."""

    data = await state.get_data()

    await state.set_state(LeadForm.confirmation)

    await message.answer(
        build_lead_summary(data),
        parse_mode="HTML",
        reply_markup=get_confirmation_keyboard(
            show_admin_panel=should_show_admin_panel(message),
        ),
    )


@router.message(
    IsAdmin(),
    F.text == ADMIN_PANEL_BUTTON,
)
async def handle_admin_panel_from_form(
    message: Message,
    state: FSMContext,
) -> None:
    """Leave the lead form and open the administrator panel."""

    await state.clear()
    await show_admin_panel(message)


@router.message(F.text == DISCUSS_PROJECT_BUTTON)
async def handle_discuss_project(
    message: Message,
    state: FSMContext,
) -> None:
    """Start the lead form from the main menu."""

    await start_lead_form(message, state)


@router.message(F.text == CANCEL_BUTTON)
async def handle_cancel(
    message: Message,
    state: FSMContext,
) -> None:
    """Cancel the current form."""

    current_state = await state.get_state()

    if current_state is None:
        await message.answer(
            "Сейчас нет активной заявки.",
            reply_markup=get_main_menu_keyboard(
                show_admin_panel=should_show_admin_panel(message),
            ),
        )
        return

    await state.clear()

    await message.answer(
        "Заполнение заявки отменено.",
        reply_markup=get_main_menu_keyboard(
            show_admin_panel=should_show_admin_panel(message),
        ),
    )


@router.message(
    LeadForm.name_choice,
    F.text == USE_PROFILE_NAME_BUTTON,
)
async def handle_profile_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Use the name from the Telegram profile."""

    data = await state.get_data()
    profile_name = data.get("profile_name")

    if not profile_name:
        await message.answer(
            "Не удалось получить имя из профиля. "
            "Выберите «Указать другое имя»."
        )
        return

    await state.update_data(name=str(profile_name))
    await ask_for_contact(message, state)


@router.message(
    LeadForm.name_choice,
    F.text == ENTER_CUSTOM_NAME_BUTTON,
)
async def handle_custom_name_choice(
    message: Message,
    state: FSMContext,
) -> None:
    """Request a custom name from the client."""

    await state.set_state(LeadForm.custom_name)

    await message.answer(
        "Введите имя, которое следует использовать для обращения.",
        reply_markup=get_cancel_keyboard(
            show_admin_panel=should_show_admin_panel(message),
        ),
    )


@router.message(LeadForm.name_choice)
async def handle_invalid_name_choice(message: Message) -> None:
    """Reject an unsupported name-selection response."""

    await message.answer(
        "Используйте одну из кнопок:\n\n"
        "• «Использовать имя из профиля»;\n"
        "• «Указать другое имя»;\n"
        "• «Отменить»."
    )


@router.message(LeadForm.custom_name)
async def handle_custom_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Save the custom client name."""

    name = get_message_text(message)

    if name is None or len(name) < 2:
        await message.answer(
            "Введите имя текстом. Минимум два символа."
        )
        return

    await state.update_data(name=name)
    await ask_for_contact(message, state)


@router.message(LeadForm.contact, F.contact)
async def handle_contact(
    message: Message,
    state: FSMContext,
) -> None:
    """Save the contact shared by the current user."""

    contact = message.contact
    user = message.from_user

    if contact is None or user is None:
        await message.answer(
            "Не удалось получить контакт. "
            "Нажмите кнопку «Поделиться контактом»."
        )
        return

    if contact.user_id != user.id:
        await message.answer(
            "Передайте именно свой контакт через кнопку "
            "«Поделиться контактом»."
        )
        return

    await state.update_data(
        contact_phone=contact.phone_number,
        contact_first_name=contact.first_name,
        contact_last_name=contact.last_name or "",
        telegram_user_id=user.id,
        telegram_username=user.username,
    )

    await state.set_state(LeadForm.project_description)

    await message.answer(
        "Контакт сохранён.\n\n"
        "Опишите проект: для чего нужен бот "
        "и какую задачу он должен решать?",
        reply_markup=get_cancel_keyboard(
            show_admin_panel=should_show_admin_panel(message),
        ),
    )


@router.message(LeadForm.contact)
async def handle_invalid_contact(message: Message) -> None:
    """Reject messages that do not contain a shared contact."""

    await message.answer(
        "На этом этапе нажмите кнопку "
        "«Поделиться контактом».\n\n"
        "Вводить номер телефона вручную не нужно."
    )


@router.message(LeadForm.project_description)
async def handle_project_description(
    message: Message,
    state: FSMContext,
) -> None:
    """Save the project description."""

    project_description = get_message_text(message)

    if project_description is None or len(project_description) < 10:
        await message.answer(
            "Опишите проект подробнее — минимум 10 символов."
        )
        return

    await state.update_data(
        project_description=project_description,
    )
    await state.set_state(LeadForm.required_features)

    await message.answer(
        "Перечислите необходимые функции.\n\n"
        "Например: регистрация, анкета, приём оплаты, "
        "уведомления, интеграция с CRM."
    )


@router.message(LeadForm.required_features)
async def handle_required_features(
    message: Message,
    state: FSMContext,
) -> None:
    """Save the required features."""

    required_features = get_message_text(message)

    if required_features is None or len(required_features) < 5:
        await message.answer(
            "Перечислите необходимые функции подробнее."
        )
        return

    await state.update_data(
        required_features=required_features,
    )
    await state.set_state(LeadForm.deadline)

    await message.answer(
        "Когда желательно запустить проект?\n\n"
        "Можно указать точную дату или примерный срок."
    )


@router.message(LeadForm.deadline)
async def handle_deadline(
    message: Message,
    state: FSMContext,
) -> None:
    """Save the desired deadline."""

    deadline = get_message_text(message)

    if deadline is None:
        await message.answer(
            "Укажите желаемый срок текстом."
        )
        return

    await state.update_data(deadline=deadline)
    await state.set_state(LeadForm.budget)

    await message.answer(
        "Какой ориентировочный бюджет предусмотрен на проект?"
    )


@router.message(LeadForm.budget)
async def handle_budget(
    message: Message,
    state: FSMContext,
) -> None:
    """Save the estimated budget."""

    budget = get_message_text(message)

    if budget is None:
        await message.answer(
            "Укажите ориентировочный бюджет текстом."
        )
        return

    await state.update_data(budget=budget)
    await state.set_state(LeadForm.comment)

    await message.answer(
        "Добавьте комментарий или важные детали.\n\n"
        "Этот шаг можно пропустить.",
        reply_markup=get_comment_keyboard(
            show_admin_panel=should_show_admin_panel(message),
        ),
    )


@router.message(
    LeadForm.comment,
    F.text == SKIP_BUTTON,
)
async def handle_skip_comment(
    message: Message,
    state: FSMContext,
) -> None:
    """Skip the optional comment."""

    await state.update_data(
        comment="Не указан",
        attachments=[],
    )
    await ask_for_attachments(message, state)


@router.message(LeadForm.comment)
async def handle_comment(
    message: Message,
    state: FSMContext,
) -> None:
    """Save the additional comment."""

    comment = get_message_text(message)

    if comment is None:
        await message.answer(
            "Отправьте комментарий текстом "
            "или нажмите «Пропустить»."
        )
        return

    await state.update_data(
        comment=comment,
        attachments=[],
    )
    await ask_for_attachments(message, state)


@router.message(
    LeadForm.attachments,
    F.text == DONE_ATTACHMENTS_BUTTON,
)
async def handle_attachments_done(
    message: Message,
    state: FSMContext,
) -> None:
    """Finish attachment collection when at least one file exists."""

    data = await state.get_data()
    attachments = data.get("attachments") or []

    if not attachments:
        await message.answer(
            "Вложения пока не добавлены. "
            "Отправьте файл или нажмите «Без вложений»."
        )
        return

    await show_confirmation(message, state)


@router.message(
    LeadForm.attachments,
    F.text == SKIP_ATTACHMENTS_BUTTON,
)
async def handle_skip_attachments(
    message: Message,
    state: FSMContext,
) -> None:
    """Continue without attachments when none were collected."""

    data = await state.get_data()
    attachments = data.get("attachments") or []

    if attachments:
        await message.answer(
            "Уже добавлены вложения. "
            "Нажмите «Готово», чтобы сохранить их."
        )
        return

    await state.update_data(attachments=[])
    await show_confirmation(message, state)


@router.message(
    LeadForm.attachments,
    F.document | F.photo | F.video | F.audio | F.voice,
)
async def handle_attachment(
    message: Message,
    state: FSMContext,
) -> None:
    """Collect one supported Telegram attachment."""

    attachment = get_attachment_data(message)

    if attachment is None:
        await message.answer(
            "Этот тип вложения не поддерживается."
        )
        return

    data = await state.get_data()
    attachments = list(data.get("attachments") or [])

    if len(attachments) >= MAX_ATTACHMENTS:
        await message.answer(
            "Достигнут лимит: 10 вложений. "
            "Нажмите «Готово»."
        )
        return

    unique_id = attachment["telegram_file_unique_id"]

    if any(
        item.get("telegram_file_unique_id") == unique_id
        for item in attachments
    ):
        await message.answer(
            "Этот файл уже добавлен."
        )
        return

    attachments.append(attachment)
    await state.update_data(attachments=attachments)

    await message.answer(
        f"Добавлено: {get_attachment_label(attachment)}.\n"
        f"Вложений: {len(attachments)} из {MAX_ATTACHMENTS}."
    )


@router.message(LeadForm.attachments)
async def handle_invalid_attachment(message: Message) -> None:
    """Reject unsupported input during attachment collection."""

    await message.answer(
        "Отправьте документ, фотографию, видео, аудио "
        "или голосовое сообщение.\n\n"
        "Затем нажмите «Готово» или «Без вложений»."
    )


@router.message(
    LeadForm.confirmation,
    F.text == RESTART_BUTTON,
)
async def handle_restart(
    message: Message,
    state: FSMContext,
) -> None:
    """Restart the project request form."""

    await start_lead_form(message, state)


@router.message(
    LeadForm.confirmation,
    F.text == CONFIRM_BUTTON,
)
async def handle_confirmation(
    message: Message,
    state: FSMContext,
) -> None:
    """Persist and confirm the collected project request."""

    data = await state.get_data()
    settings = get_settings()

    try:
        submission = LeadSubmission.from_fsm_data(data)
        lead_id = await create_lead(submission)
    except (KeyError, ValueError, SQLAlchemyError):
        logger.exception(
            "Failed to persist a project request"
        )

        await message.answer(
            "Не удалось сохранить заявку.\n\n"
            "Попробуйте подтвердить её повторно. "
            "Если ошибка сохранится, заполните заявку заново.",
            reply_markup=get_confirmation_keyboard(
                show_admin_panel=should_show_admin_panel(message),
            ),
        )
        return

    summary = build_lead_summary(data)

    # Заявка уже сохранена в PostgreSQL.
    # Повторное подтверждение больше не требуется.
    await state.clear()

    notifications_enabled = False

    try:
        notifications_enabled = (
            await admin_notifications_enabled(
                settings.admin_chat_id
            )
        )
    except SQLAlchemyError:
        logger.exception(
            "Failed to read notification settings "
            "for lead %s",
            lead_id,
        )

    if notifications_enabled:
        try:
            await send_lead_to_admin(
                bot=message.bot,
                admin_chat_id=settings.admin_chat_id,
                lead_id=lead_id,
                summary=summary,
                data=data,
            )
        except TelegramAPIError:
            logger.exception(
                "Lead %s was saved, "
                "but admin notification failed",
                lead_id,
            )

    await message.answer(
        f"Заявка №{lead_id} принята и сохранена.\n\n"
        "Panini свяжется с вами для уточнения деталей "
        "и согласования дальнейшей работы.",
        reply_markup=get_main_menu_keyboard(
            show_admin_panel=should_show_admin_panel(message),
        ),
    )


@router.message(LeadForm.confirmation)
async def handle_invalid_confirmation(message: Message) -> None:
    """Reject an unsupported confirmation response."""

    await message.answer(
        "Используйте кнопки «Подтвердить заявку», "
        "«Заполнить заново» или «Отменить»."
    )
