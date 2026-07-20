from collections.abc import Collection
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.enums import LeadStatus
from app.database.models.lead import (
    Lead,
    LeadAdminComment,
    LeadStatusHistory,
)


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

    async def change_status(
        self,
        *,
        lead_id: int,
        allowed_from: Collection[LeadStatus],
        new_status: LeadStatus,
        admin_telegram_id: int,
        comment: str,
    ) -> tuple[Lead | None, bool]:
        """Change a lead status and append a history record."""

        statement = (
            select(Lead)
            .where(Lead.id == lead_id)
            .with_for_update()
        )

        lead = await self._session.scalar(statement)

        if lead is None:
            return None, False

        if lead.status not in allowed_from:
            return lead, False

        old_status = lead.status
        lead.status = new_status

        history = LeadStatusHistory(
            lead_id=lead.id,
            old_status=old_status,
            new_status=new_status,
            admin_telegram_id=admin_telegram_id,
            comment=comment,
        )

        self._session.add(history)
        await self._session.flush()

        return lead, True

    async def close(
        self,
        *,
        lead_id: int,
        allowed_from: Collection[LeadStatus],
        admin_telegram_id: int,
        comment: str,
    ) -> tuple[
        Lead | None,
        bool,
        LeadAdminComment | None,
    ]:
        """Close a lead and save its closing comment."""

        statement = (
            select(Lead)
            .options(selectinload(Lead.user))
            .where(Lead.id == lead_id)
            .with_for_update()
        )

        lead = await self._session.scalar(statement)

        if lead is None:
            return None, False, None

        if lead.status not in allowed_from:
            return lead, False, None

        old_status = lead.status

        lead.status = LeadStatus.CLOSED
        lead.close_comment = comment
        lead.closed_at = datetime.now(timezone.utc)

        history = LeadStatusHistory(
            lead_id=lead.id,
            old_status=old_status,
            new_status=LeadStatus.CLOSED,
            admin_telegram_id=admin_telegram_id,
            comment=comment,
        )

        admin_comment = LeadAdminComment(
            lead_id=lead.id,
            admin_telegram_id=admin_telegram_id,
            comment=comment,
            is_sent_to_client=False,
        )

        self._session.add_all(
            [
                history,
                admin_comment,
            ]
        )

        await self._session.flush()

        return lead, True, admin_comment

    async def mark_admin_comment_delivery(
        self,
        *,
        comment_id: int,
        delivered: bool,
        error_message: str | None,
    ) -> bool:
        """Store the delivery result of an admin comment."""

        statement = (
            select(LeadAdminComment)
            .where(
                LeadAdminComment.id == comment_id
            )
            .with_for_update()
        )

        admin_comment = await self._session.scalar(
            statement
        )

        if admin_comment is None:
            return False

        admin_comment.is_sent_to_client = delivered
        admin_comment.delivery_error = error_message

        await self._session.flush()

        return True