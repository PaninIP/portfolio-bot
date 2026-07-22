from enum import StrEnum

from sqlalchemy import Enum as SqlEnum


class LeadStatus(StrEnum):
    """Available project request statuses."""

    NEW = "new"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_CLIENT = "waiting_for_client"
    CLOSED = "closed"


class AttachmentType(StrEnum):
    """Supported project-request attachment types."""

    DOCUMENT = "document"
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    VOICE = "voice"


class NotificationType(StrEnum):
    """Types of notifications sent by the bot."""

    NEW_LEAD = "new_lead"
    LEAD_STATUS_CHANGED = "lead_status_changed"
    LEAD_CLOSED = "lead_closed"


class DeliveryStatus(StrEnum):
    """Notification delivery statuses."""

    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"


def get_enum_values(
    enum_class: type[StrEnum],
) -> list[str]:
    """Return database values from a string enumeration."""

    return [item.value for item in enum_class]


lead_status_enum = SqlEnum(
    LeadStatus,
    name="lead_status",
    values_callable=get_enum_values,
    validate_strings=True,
)

notification_type_enum = SqlEnum(
    NotificationType,
    name="notification_type",
    values_callable=get_enum_values,
    validate_strings=True,
)

delivery_status_enum = SqlEnum(
    DeliveryStatus,
    name="delivery_status",
    values_callable=get_enum_values,
    validate_strings=True,
)

attachment_type_enum = SqlEnum(
    AttachmentType,
    name="attachment_type",
    values_callable=get_enum_values,
    validate_strings=True,
)
