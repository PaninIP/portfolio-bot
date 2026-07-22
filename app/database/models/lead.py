from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.enums import (
    AttachmentType,
    LeadStatus,
    attachment_type_enum,
    lead_status_enum,
)
from app.database.mixins import CreatedAtMixin, TimestampMixin


if TYPE_CHECKING:
    from app.database.models.notification import NotificationLog
    from app.database.models.user import User


class Lead(TimestampMixin, Base):
    """Project request submitted by a Telegram user."""

    __tablename__ = "leads"

    __table_args__ = (
        Index(
            "ix_leads_status_created_at",
            "status",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    contact_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    project_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    required_features: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    deadline: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    budget: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    client_comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[LeadStatus] = mapped_column(
        lead_status_enum,
        nullable=False,
        default=LeadStatus.NEW,
        server_default=LeadStatus.NEW.value,
        index=True,
    )

    close_comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped[User] = relationship(
        back_populates="leads",
    )

    status_history: Mapped[list[LeadStatusHistory]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
        order_by="LeadStatusHistory.created_at",
    )

    admin_comments: Mapped[list[LeadAdminComment]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
        order_by="LeadAdminComment.created_at",
    )

    notifications: Mapped[list[NotificationLog]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
        order_by="NotificationLog.created_at",
    )

    attachments: Mapped[list[LeadAttachment]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
        order_by="LeadAttachment.created_at",
    )


class LeadAttachment(CreatedAtMixin, Base):
    """Telegram file attached to a project request."""

    __tablename__ = "lead_attachments"

    __table_args__ = (
        Index(
            "ix_lead_attachments_lead_created_at",
            "lead_id",
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

    attachment_type: Mapped[AttachmentType] = mapped_column(
        attachment_type_enum,
        nullable=False,
    )

    telegram_file_id: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )

    telegram_file_unique_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    file_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    mime_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    file_size: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    caption: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    lead: Mapped[Lead] = relationship(
        back_populates="attachments",
    )


class LeadStatusHistory(CreatedAtMixin, Base):
    """History of changes to a project request status."""

    __tablename__ = "lead_status_history"

    __table_args__ = (
        Index(
            "ix_lead_status_history_lead_created_at",
            "lead_id",
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

    old_status: Mapped[LeadStatus | None] = mapped_column(
        lead_status_enum,
        nullable=True,
    )

    new_status: Mapped[LeadStatus] = mapped_column(
        lead_status_enum,
        nullable=False,
    )

    admin_telegram_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    lead: Mapped[Lead] = relationship(
        back_populates="status_history",
    )


class LeadAdminComment(CreatedAtMixin, Base):
    """Administrative comment related to a project request."""

    __tablename__ = "lead_admin_comments"

    __table_args__ = (
        Index(
            "ix_lead_admin_comments_lead_created_at",
            "lead_id",
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

    admin_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    comment: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_sent_to_client: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )

    delivery_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    lead: Mapped[Lead] = relationship(
        back_populates="admin_comments",
    )