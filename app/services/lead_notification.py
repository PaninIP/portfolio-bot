from collections.abc import Sequence
from html import escape
from typing import Any

from aiogram import Bot

from app.database.enums import AttachmentType
from app.database.models.lead import LeadAttachment


def build_client_profile_link(
    data: dict[str, Any],
) -> str:
    """Build an HTML link to the client's Telegram profile."""

    username = data.get("telegram_username")
    telegram_user_id = data.get("telegram_user_id")

    contact_name = " ".join(
        part
        for part in (
            data.get("contact_first_name"),
            data.get("contact_last_name"),
        )
        if part
    ).strip()

    link_text = escape(
        contact_name or "Открыть профиль клиента"
    )

    if username:
        profile_url = f"https://t.me/{username}"
    elif telegram_user_id:
        profile_url = f"tg://user?id={telegram_user_id}"
    else:
        return link_text

    return f'<a href="{profile_url}">{link_text}</a>'


def build_admin_notification(
    *,
    lead_id: int,
    summary: str,
    data: dict[str, Any],
) -> str:
    """Build a notification about a new project request."""

    profile_link = build_client_profile_link(data)

    return (
        f"<b>Новая заявка №{lead_id}</b>\n\n"
        f"<b>Профиль клиента:</b> {profile_link}\n\n"
        f"{summary}"
    )


def build_attachment_caption(
    *,
    lead_id: int,
    position: int,
    total: int,
    original_caption: str | None,
) -> str:
    """Build a safe Telegram media caption."""

    prefix = (
        f"📎 Заявка №{lead_id} · "
        f"вложение {position} из {total}"
    )

    if not original_caption:
        return prefix

    available = max(0, 1024 - len(prefix) - 2)
    trimmed = original_caption[:available]

    return f"{prefix}\n\n{trimmed}"


async def send_attachment_by_file_id(
    *,
    bot: Bot,
    chat_id: int,
    attachment_type: AttachmentType,
    file_id: str,
    caption: str,
) -> None:
    """Send one stored Telegram file by its reusable file ID."""

    if attachment_type == AttachmentType.DOCUMENT:
        await bot.send_document(
            chat_id=chat_id,
            document=file_id,
            caption=caption,
        )
        return

    if attachment_type == AttachmentType.PHOTO:
        await bot.send_photo(
            chat_id=chat_id,
            photo=file_id,
            caption=caption,
        )
        return

    if attachment_type == AttachmentType.VIDEO:
        await bot.send_video(
            chat_id=chat_id,
            video=file_id,
            caption=caption,
        )
        return

    if attachment_type == AttachmentType.AUDIO:
        await bot.send_audio(
            chat_id=chat_id,
            audio=file_id,
            caption=caption,
        )
        return

    if attachment_type == AttachmentType.VOICE:
        await bot.send_voice(
            chat_id=chat_id,
            voice=file_id,
            caption=caption,
        )
        return

    raise ValueError(
        f"Unsupported attachment type: {attachment_type}"
    )


async def send_submission_attachments(
    *,
    bot: Bot,
    chat_id: int,
    lead_id: int,
    attachments: Sequence[dict[str, Any]],
) -> None:
    """Send attachments kept in FSM storage after lead creation."""

    total = len(attachments)

    for position, attachment in enumerate(
        attachments,
        start=1,
    ):
        await send_attachment_by_file_id(
            bot=bot,
            chat_id=chat_id,
            attachment_type=AttachmentType(
                attachment["attachment_type"]
            ),
            file_id=str(attachment["telegram_file_id"]),
            caption=build_attachment_caption(
                lead_id=lead_id,
                position=position,
                total=total,
                original_caption=attachment.get("caption"),
            ),
        )


async def send_stored_lead_attachments(
    *,
    bot: Bot,
    chat_id: int,
    lead_id: int,
    attachments: Sequence[LeadAttachment],
) -> None:
    """Send attachments loaded from the database."""

    total = len(attachments)

    for position, attachment in enumerate(
        attachments,
        start=1,
    ):
        await send_attachment_by_file_id(
            bot=bot,
            chat_id=chat_id,
            attachment_type=attachment.attachment_type,
            file_id=attachment.telegram_file_id,
            caption=build_attachment_caption(
                lead_id=lead_id,
                position=position,
                total=total,
                original_caption=attachment.caption,
            ),
        )


async def send_lead_to_admin(
    *,
    bot: Bot,
    admin_chat_id: int,
    lead_id: int,
    summary: str,
    data: dict[str, Any],
) -> None:
    """Send a confirmed project request to the administrator."""

    notification = build_admin_notification(
        lead_id=lead_id,
        summary=summary,
        data=data,
    )

    await bot.send_message(
        chat_id=admin_chat_id,
        text=notification,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    attachments = data.get("attachments") or []

    if attachments:
        await send_submission_attachments(
            bot=bot,
            chat_id=admin_chat_id,
            lead_id=lead_id,
            attachments=attachments,
        )


async def send_lead_closed_to_client(
    *,
    bot: Bot,
    client_telegram_id: int,
    lead_id: int,
    comment: str,
) -> None:
    """Notify a client that their lead has been closed."""

    await bot.send_message(
        chat_id=client_telegram_id,
        text=(
            f"<b>Ваша заявка №{lead_id} закрыта.</b>\n\n"
            f"<b>Комментарий:</b>\n"
            f"{escape(comment)}\n\n"
            "При необходимости вы можете оставить "
            "новую заявку."
        ),
        parse_mode="HTML",
    )
