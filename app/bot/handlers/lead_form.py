from html import escape
from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards.lead_form import (
    CANCEL_BUTTON,
    CONFIRM_BUTTON,
    ENTER_CUSTOM_NAME_BUTTON,
    RESTART_BUTTON,
    SKIP_BUTTON,
    USE_PROFILE_NAME_BUTTON,
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
        f"{format_html(data.get('comment', 'не указан'))}"
    )


async def ask_for_contact(
    message: Message,
    state: FSMContext,
) -> None:
    """Request the client's Telegram contact."""

    await state.set_state(LeadForm.contact)

    await message.answer(
        "Передайте контакт Telegram, чтобы Иван мог связаться с вами.\n\n"
        "Telegram запросит подтверждение перед отправкой номера.",
        reply_markup=get_contact_keyboard(),
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
        reply_markup=get_name_choice_keyboard(),
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
        reply_markup=get_confirmation_keyboard(),
    )


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
            reply_markup=get_main_menu_keyboard(),
        )
        return

    await state.clear()

    await message.answer(
        "Заполнение заявки отменено.",
        reply_markup=get_main_menu_keyboard(),
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
        reply_markup=get_cancel_keyboard(),
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
        reply_markup=get_cancel_keyboard(),
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
        reply_markup=get_comment_keyboard(),
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

    await state.update_data(comment="Не указан")
    await show_confirmation(message, state)


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

    await state.update_data(comment=comment)
    await show_confirmation(message, state)


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
    """Confirm the collected project request."""

    await state.clear()

    await message.answer(
        "Заявка принята.\n\n"
        "Иван свяжется с вами для уточнения деталей "
        "и согласования дальнейшей работы.",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(LeadForm.confirmation)
async def handle_invalid_confirmation(message: Message) -> None:
    """Reject an unsupported confirmation response."""

    await message.answer(
        "Используйте кнопки «Подтвердить заявку», "
        "«Заполнить заново» или «Отменить»."
    )