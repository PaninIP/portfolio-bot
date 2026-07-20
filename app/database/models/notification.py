from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.enums import (
    DeliveryStatus,
    NotificationType,
    delivery_status_enum,
    notification_type_enum,
)
from app.database.mixins import CreatedAtMixin


if TYPE_CHECKING:
    from app.database.models.lead import Lead


class NotificationLog(CreatedAtMixin, Base):
    """Result of an attempted Telegram notification."""

    __tablename__ = "notification_log"

    __table_args__ = (
        Index(
            "ix_notification_log_lead_created_at",
            "lead_id",
            "created_at",
        ),
        Index(
            "ix_notification_log_recipient_created_at",
            "recipient_telegram_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    lead_id: Mapped[int] = mapped_column(
        ForeignKey(
            "leads.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    recipient_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    notification_type: Mapped[NotificationType] = mapped_column(
        notification_type_enum,
        nullable=False,
    )

    delivery_status: Mapped[DeliveryStatus] = mapped_column(
        delivery_status_enum,
        nullable=False,
        default=DeliveryStatus.PENDING,
        server_default=DeliveryStatus.PENDING.value,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    lead: Mapped[Lead] = relationship(
        back_populates="notifications",
    )