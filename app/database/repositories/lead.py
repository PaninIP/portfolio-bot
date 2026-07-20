from sqlalchemy.ext.asyncio import AsyncSession

from app.database.enums import LeadStatus
from app.database.models.lead import Lead, LeadStatusHistory


class LeadRepository:
    """Provide database operations for project requests."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: int,
        contact_name: str,
        project_description: str,
        required_features: str,
        deadline: str,
        budget: str,
        client_comment: str | None,
    ) -> Lead:
        """Create a lead and its initial status-history record."""

        lead = Lead(
            user_id=user_id,
            contact_name=contact_name,
            project_description=project_description,
            required_features=required_features,
            deadline=deadline,
            budget=budget,
            client_comment=client_comment,
            status=LeadStatus.NEW,
        )

        self._session.add(lead)
        await self._session.flush()

        status_history = LeadStatusHistory(
            lead_id=lead.id,
            old_status=None,
            new_status=LeadStatus.NEW,
            admin_telegram_id=None,
            comment="Заявка создана пользователем",
        )

        self._session.add(status_history)
        await self._session.flush()

        return lead