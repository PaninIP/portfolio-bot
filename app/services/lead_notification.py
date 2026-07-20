from html import escape
from typing import Any

from aiogram import Bot


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