from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.database.repositories import LeadRepository, UserRepository
from app.database.session import async_session_factory


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

        return lead.id