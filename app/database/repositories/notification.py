from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.enums import (
    DeliveryStatus,
    NotificationType,
)
from app.database.models.notification import NotificationLog


class NotificationRepository:
    """Provide database operations for notification logs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        lead_id: int,
        recipient_telegram_id: int,
        notification_type: NotificationType,
        delivery_status: DeliveryStatus,
        error_message: str | None,
        delivered_at: datetime | None,
    ) -> NotificationLog:
        """Create a notification delivery record."""

        notification = NotificationLog(
            lead_id=lead_id,
            recipient_telegram_id=recipient_telegram_id,
            notification_type=notification_type,
            delivery_status=delivery_status,
            error_message=error_message,
            delivered_at=delivered_at,
        )

        self._session.add(notification)
        await self._session.flush()

        return notification