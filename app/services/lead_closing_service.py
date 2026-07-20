from dataclasses import dataclass
from datetime import datetime, timezone

from app.database.enums import (
    DeliveryStatus,
    LeadStatus,
    NotificationType,
)
from app.database.repositories import (
    LeadRepository,
    NotificationRepository,
)
from app.database.session import async_session_factory


@dataclass(frozen=True, slots=True)
class LeadCloseResult:
    """Result of a lead-closing operation."""

    found: bool
    changed: bool
    current_status: LeadStatus | None
    lead_id: int | None
    client_telegram_id: int | None
    admin_comment_id: int | None
    close_comment: str | None


async def close_lead(
    *,
    lead_id: int,
    admin_telegram_id: int,
    comment: str,
) -> LeadCloseResult:
    """Close a lead atomically."""

    async with async_session_factory() as session:
        async with session.begin():
            repository = LeadRepository(session)

            lead, changed, admin_comment = (
                await repository.close(
                    lead_id=lead_id,
                    allowed_from=(
                        LeadStatus.NEW,
                        LeadStatus.IN_PROGRESS,
                        LeadStatus.WAITING_FOR_CLIENT,
                    ),
                    admin_telegram_id=admin_telegram_id,
                    comment=comment,
                )
            )

            if lead is None:
                return LeadCloseResult(
                    found=False,
                    changed=False,
                    current_status=None,
                    lead_id=None,
                    client_telegram_id=None,
                    admin_comment_id=None,
                    close_comment=None,
                )

            return LeadCloseResult(
                found=True,
                changed=changed,
                current_status=lead.status,
                lead_id=lead.id,
                client_telegram_id=(
                    lead.user.telegram_user_id
                ),
                admin_comment_id=(
                    admin_comment.id
                    if admin_comment
                    else None
                ),
                close_comment=lead.close_comment,
            )


async def record_close_notification_delivery(
    *,
    lead_id: int,
    admin_comment_id: int,
    recipient_telegram_id: int,
    delivered: bool,
    error_message: str | None,
) -> None:
    """Store the result of a closing notification."""

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
            lead_repository = LeadRepository(session)
            notification_repository = (
                NotificationRepository(session)
            )

            await lead_repository.mark_admin_comment_delivery(
                comment_id=admin_comment_id,
                delivered=delivered,
                error_message=error_message,
            )

            await notification_repository.create(
                lead_id=lead_id,
                recipient_telegram_id=(
                    recipient_telegram_id
                ),
                notification_type=(
                    NotificationType.LEAD_CLOSED
                ),
                delivery_status=delivery_status,
                error_message=error_message,
                delivered_at=delivered_at,
            )