from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.database.enums import AttachmentType
from app.database.repositories import LeadRepository, UserRepository
from app.database.session import async_session_factory


class LeadAttachmentSubmission(BaseModel):
    """Validated Telegram attachment metadata from the lead form."""

    attachment_type: AttachmentType
    telegram_file_id: str = Field(min_length=1, max_length=512)
    telegram_file_unique_id: str = Field(
        min_length=1,
        max_length=128,
    )
    file_name: str | None = Field(
        default=None,
        max_length=255,
    )
    mime_type: str | None = Field(
        default=None,
        max_length=255,
    )
    file_size: int | None = Field(default=None, ge=0)
    caption: str | None = Field(default=None, max_length=1024)


class LeadSubmission(BaseModel):
    """Validated data collected by the lead form."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    telegram_user_id: int
    telegram_username: str | None = None

    contact_first_name: str = Field(min_length=1, max_length=255)
    contact_last_name: str | None = Field(
        default=None,
        max_length=255,
    )
    contact_phone: str | None = Field(
        default=None,
        max_length=32,
    )

    contact_name: str = Field(min_length=2, max_length=255)
    project_description: str = Field(min_length=10)
    required_features: str = Field(min_length=5)
    deadline: str = Field(min_length=1, max_length=255)
    budget: str = Field(min_length=1, max_length=255)
    client_comment: str | None = None
    attachments: list[LeadAttachmentSubmission] = Field(
        default_factory=list,
        max_length=10,
    )

    @classmethod
    def from_fsm_data(
        cls,
        data: dict[str, Any],
    ) -> "LeadSubmission":
        """Create validated submission data from FSM storage."""

        comment = data.get("comment")

        return cls(
            telegram_user_id=data["telegram_user_id"],
            telegram_username=data.get("telegram_username"),
            contact_first_name=data["contact_first_name"],
            contact_last_name=data.get("contact_last_name") or None,
            contact_phone=data.get("contact_phone") or None,
            contact_name=data["name"],
            project_description=data["project_description"],
            required_features=data["required_features"],
            deadline=data["deadline"],
            budget=data["budget"],
            client_comment=(
                None
                if comment in (None, "", "Не указан")
                else str(comment)
            ),
            attachments=data.get("attachments") or [],
        )


async def create_lead(
    submission: LeadSubmission,
) -> int:
    """Persist a user, lead, and initial status history atomically."""

    async with async_session_factory() as session:
        async with session.begin():
            user_repository = UserRepository(session)
            lead_repository = LeadRepository(session)

            user = await user_repository.upsert(
                telegram_user_id=submission.telegram_user_id,
                username=submission.telegram_username,
                first_name=submission.contact_first_name,
                last_name=submission.contact_last_name,
                phone=submission.contact_phone,
            )

            lead = await lead_repository.create(
                user_id=user.id,
                contact_name=submission.contact_name,
                project_description=submission.project_description,
                required_features=submission.required_features,
                deadline=submission.deadline,
                budget=submission.budget,
                client_comment=submission.client_comment,
            )

            for attachment in submission.attachments:
                await lead_repository.create_attachment(
                    lead_id=lead.id,
                    attachment_type=attachment.attachment_type,
                    telegram_file_id=attachment.telegram_file_id,
                    telegram_file_unique_id=(
                        attachment.telegram_file_unique_id
                    ),
                    file_name=attachment.file_name,
                    mime_type=attachment.mime_type,
                    file_size=attachment.file_size,
                    caption=attachment.caption,
                )

        return lead.id