from collections.abc import Collection

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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

        history = LeadStatusHistory(
            lead_id=lead.id,
            old_status=None,
            new_status=LeadStatus.NEW,
            admin_telegram_id=None,
            comment="Заявка создана пользователем",
        )

        self._session.add(history)
        await self._session.flush()

        return lead

    async def get_status_counts(
        self,
    ) -> dict[LeadStatus, int]:
        """Return lead counts grouped by status."""

        statement = (
            select(
                Lead.status,
                func.count(Lead.id),
            )
            .group_by(Lead.status)
        )

        result = await self._session.execute(statement)

        return {
            status: int(count)
            for status, count in result.all()
        }

    async def count_by_statuses(
        self,
        statuses: Collection[LeadStatus],
    ) -> int:
        """Count leads having one of the specified statuses."""

        statement = (
            select(func.count(Lead.id))
            .where(Lead.status.in_(statuses))
        )

        count = await self._session.scalar(statement)

        return int(count or 0)

    async def list_by_statuses(
        self,
        statuses: Collection[LeadStatus],
        *,
        limit: int,
        offset: int,
    ) -> list[Lead]:
        """Return a page of leads with their users."""

        statement = (
            select(Lead)
            .options(selectinload(Lead.user))
            .where(Lead.status.in_(statuses))
            .order_by(
                Lead.created_at.desc(),
                Lead.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.scalars(statement)

        return list(result.all())

    async def get_by_id_with_user(
        self,
        lead_id: int,
    ) -> Lead | None:
        """Return a lead with its Telegram user."""

        statement = (
            select(Lead)
            .options(selectinload(Lead.user))
            .where(Lead.id == lead_id)
        )

        return await self._session.scalar(statement)