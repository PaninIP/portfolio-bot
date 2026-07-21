from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from math import ceil

from app.database.enums import (
    DeliveryStatus,
    LeadStatus,
    NotificationType,
)
from app.database.models.lead import Lead
from app.database.repositories import (
    LeadRepository,
    NotificationRepository,
)
from app.database.session import async_session_factory


DEFAULT_PAGE_SIZE = 5


class LeadListType(StrEnum):
    """Available administrator lead lists."""

    NEW = "new"
    ACTIVE = "active"
    ARCHIVE = "archive"


@dataclass(frozen=True, slots=True)
class LeadPage:
    """One page of administrator lead results."""

    items: tuple[Lead, ...]
    list_type: LeadListType
    page: int
    total_pages: int
    total_items: int


@dataclass(frozen=True, slots=True)
class LeadStatusChangeResult:
    """Result of an administrator status-change operation."""

    found: bool
    changed: bool
    current_status: LeadStatus | None


@dataclass(frozen=True, slots=True)
class LeadReopenResult:
    """Result of returning a closed lead to active work."""

    found: bool
    changed: bool
    current_status: LeadStatus | None
    lead_id: int | None
    client_telegram_id: int | None


def get_list_statuses(
    list_type: LeadListType,
) -> tuple[LeadStatus, ...]:
    """Return statuses included in an administrator list."""

    if list_type == LeadListType.NEW:
        return (LeadStatus.NEW,)

    if list_type == LeadListType.ARCHIVE:
        return (LeadStatus.CLOSED,)

    return (
        LeadStatus.IN_PROGRESS,
        LeadStatus.WAITING_FOR_CLIENT,
    )


async def get_lead_page(
    *,
    list_type: LeadListType,
    page: int,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> LeadPage:
    """Return one paginated lead list."""

    statuses = get_list_statuses(list_type)

    async with async_session_factory() as session:
        repository = LeadRepository(session)

        total_items = await repository.count_by_statuses(
            statuses
        )

        total_pages = max(
            1,
            ceil(total_items / page_size),
        )

        normalized_page = min(
            max(page, 1),
            total_pages,
        )

        leads = await repository.list_by_statuses(
            statuses,
            limit=page_size,
            offset=(normalized_page - 1) * page_size,
        )

    return LeadPage(
        items=tuple(leads),
        list_type=list_type,
        page=normalized_page,
        total_pages=total_pages,
        total_items=total_items,
    )


async def get_admin_lead(
    lead_id: int,
) -> Lead | None:
    """Return a lead for the administrator card."""

    async with async_session_factory() as session:
        repository = LeadRepository(session)

        return await repository.get_by_id_with_user(
            lead_id
        )


async def take_lead_in_progress(
    *,
    lead_id: int,
    admin_telegram_id: int,
) -> LeadStatusChangeResult:
    """Move a new lead into active work."""

    async with async_session_factory() as session:
        async with session.begin():
            repository = LeadRepository(session)

            lead, changed = await repository.change_status(
                lead_id=lead_id,
                allowed_from=(LeadStatus.NEW,),
                new_status=LeadStatus.IN_PROGRESS,
                admin_telegram_id=admin_telegram_id,
                comment=(
                    "Заявка взята администратором в работу"
                ),
            )

            if lead is None:
                return LeadStatusChangeResult(
                    found=False,
                    changed=False,
                    current_status=None,
                )

            return LeadStatusChangeResult(
                found=True,
                changed=changed,
                current_status=lead.status,
            )


async def reopen_closed_lead(
    *,
    lead_id: int,
    admin_telegram_id: int,
) -> LeadReopenResult:
    """Return a closed lead to active work."""

    async with async_session_factory() as session:
        async with session.begin():
            repository = LeadRepository(session)

            lead, changed = await repository.reopen(
                lead_id=lead_id,
                admin_telegram_id=admin_telegram_id,
            )

            if lead is None:
                return LeadReopenResult(
                    found=False,
                    changed=False,
                    current_status=None,
                    lead_id=None,
                    client_telegram_id=None,
                )

            return LeadReopenResult(
                found=True,
                changed=changed,
                current_status=lead.status,
                lead_id=lead.id,
                client_telegram_id=(
                    lead.user.telegram_user_id
                ),
            )


async def record_reopen_notification_delivery(
    *,
    lead_id: int,
    recipient_telegram_id: int,
    delivered: bool,
    error_message: str | None,
) -> None:
    """Store the result of a lead-reopening notification."""

    delivery_status = (
        DeliveryStatus.DELIVERED
        if delivered
        else DeliveryStatus.FAILED
    )

    delivered_at = (
        datetime.now(timezone.utc)
        if delivered
        else None
    )

    async with async_session_factory() as session:
        async with session.begin():
            repository = NotificationRepository(session)

            await repository.create(
                lead_id=lead_id,
                recipient_telegram_id=(
                    recipient_telegram_id
                ),
                notification_type=(
                    NotificationType.LEAD_STATUS_CHANGED
                ),
                delivery_status=delivery_status,
                error_message=error_message,
                delivered_at=delivered_at,
            )
