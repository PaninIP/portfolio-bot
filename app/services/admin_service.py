from dataclasses import dataclass

from app.config import get_settings
from app.database.enums import LeadStatus
from app.database.repositories import (
    AdminRepository,
    LeadRepository,
)
from app.database.session import async_session_factory


@dataclass(frozen=True, slots=True)
class AdminPanelData:
    """Data displayed in the administrator panel."""

    new_leads: int
    active_leads: int
    closed_leads: int
    notifications_enabled: bool


def is_configured_admin(
    telegram_user_id: int,
) -> bool:
    """Check whether the user is listed in application settings."""

    settings = get_settings()

    return telegram_user_id == settings.admin_chat_id


async def activate_admin(
    telegram_user_id: int,
) -> bool:
    """Activate configured administrator access."""

    if not is_configured_admin(telegram_user_id):
        return False

    async with async_session_factory() as session:
        async with session.begin():
            repository = AdminRepository(session)
            admin = await repository.ensure_exists(
                telegram_user_id
            )

            return admin.is_active


async def has_admin_access(
    telegram_user_id: int,
) -> bool:
    """Check active administrator access."""

    if not is_configured_admin(telegram_user_id):
        return False

    async with async_session_factory() as session:
        repository = AdminRepository(session)
        admin = await repository.get(telegram_user_id)

        return admin is not None and admin.is_active


async def get_admin_panel_data(
    telegram_user_id: int,
) -> AdminPanelData:
    """Return statistics and settings for the admin panel."""

    async with async_session_factory() as session:
        admin_repository = AdminRepository(session)
        lead_repository = LeadRepository(session)

        admin = await admin_repository.get(
            telegram_user_id
        )

        if admin is None or not admin.is_active:
            raise PermissionError(
                "Administrator access is not active"
            )

        counts = await lead_repository.get_status_counts()

        return AdminPanelData(
            new_leads=counts.get(LeadStatus.NEW, 0),
            active_leads=(
                counts.get(LeadStatus.IN_PROGRESS, 0)
                + counts.get(
                    LeadStatus.WAITING_FOR_CLIENT,
                    0,
                )
            ),
            closed_leads=counts.get(
                LeadStatus.CLOSED,
                0,
            ),
            notifications_enabled=(
                admin.notifications_enabled
            ),
        )


async def toggle_admin_notifications(
    telegram_user_id: int,
) -> bool:
    """Toggle new-lead notifications."""

    async with async_session_factory() as session:
        async with session.begin():
            repository = AdminRepository(session)
            admin = await repository.get(
                telegram_user_id
            )

            if admin is None or not admin.is_active:
                raise PermissionError(
                    "Administrator access is not active"
                )

            return await repository.toggle_notifications(
                admin
            )


async def admin_notifications_enabled(
    telegram_user_id: int,
) -> bool:
    """Check whether notifications are enabled."""

    async with async_session_factory() as session:
        repository = AdminRepository(session)
        admin = await repository.get(
            telegram_user_id
        )

        return bool(
            admin
            and admin.is_active
            and admin.notifications_enabled
        )