from collections.abc import Collection
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.enums import LeadStatus
from app.database.models.lead import (
    Lead,
    LeadAdminComment,
    LeadStatusHistory,
)
from app.database.models.user import User


ClientSummaryRecord = tuple[
    int,
    int,
    str | None,
    str,
    str | None,
    str | None,
    int,
    int,
    int,
    datetime,
]


class LeadRepository:
    """Provide database operations for project requests."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _escape_like(value: str) -> str:
        """Escape wildcard characters used by SQL LIKE."""

        return (
            value
            .replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )

    @classmethod
    def _build_search_condition(cls, query: str):
        """Build a lead and Telegram-user search condition."""

        normalized = query.strip()
        username_query = normalized.removeprefix("@").strip()
        text_value = cls._escape_like(username_query or normalized)
        pattern = f"%{text_value}%"

        conditions = [
            Lead.contact_name.ilike(pattern, escape="\\"),
            User.username.ilike(pattern, escape="\\"),
            User.first_name.ilike(pattern, escape="\\"),
            User.last_name.ilike(pattern, escape="\\"),
            User.phone.ilike(pattern, escape="\\"),
        ]

        numeric_query = normalized.removeprefix("№").strip()

        if numeric_query.isdigit():
            numeric_value = int(numeric_query)
            conditions.extend(
                [
                    Lead.id == numeric_value,
                    User.telegram_user_id == numeric_value,
                ]
            )

        return or_(*conditions)

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

    async def count_search_results(
        self,
        query: str,
    ) -> int:
        """Count leads matching a general administrator query."""

        statement = (
            select(func.count(Lead.id))
            .join(Lead.user)
            .where(self._build_search_condition(query))
        )

        count = await self._session.scalar(statement)

        return int(count or 0)

    async def list_search_results(
        self,
        query: str,
        *,
        limit: int,
        offset: int,
    ) -> list[Lead]:
        """Return leads matching an administrator query."""

        statement = (
            select(Lead)
            .join(Lead.user)
            .options(selectinload(Lead.user))
            .where(self._build_search_condition(query))
            .order_by(
                Lead.created_at.desc(),
                Lead.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.scalars(statement)

        return list(result.all())

    async def count_created_between(
        self,
        *,
        date_from: datetime,
        date_to: datetime,
    ) -> int:
        """Count leads created in a half-open datetime period."""

        statement = (
            select(func.count(Lead.id))
            .where(
                Lead.created_at >= date_from,
                Lead.created_at < date_to,
            )
        )

        count = await self._session.scalar(statement)

        return int(count or 0)

    async def list_created_between(
        self,
        *,
        date_from: datetime,
        date_to: datetime,
        limit: int,
        offset: int,
    ) -> list[Lead]:
        """Return leads created in a half-open datetime period."""

        statement = (
            select(Lead)
            .options(selectinload(Lead.user))
            .where(
                Lead.created_at >= date_from,
                Lead.created_at < date_to,
            )
            .order_by(
                Lead.created_at.desc(),
                Lead.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.scalars(statement)

        return list(result.all())

    async def count_clients_with_leads(self) -> int:
        """Count distinct Telegram users who submitted requests."""

        statement = select(
            func.count(func.distinct(Lead.user_id))
        )

        count = await self._session.scalar(statement)

        return int(count or 0)

    def _client_summary_statement(self):
        """Build the aggregate client-directory statement."""

        total_leads = func.count(Lead.id)
        open_leads = func.count(Lead.id).filter(
            Lead.status != LeadStatus.CLOSED
        )
        closed_leads = func.count(Lead.id).filter(
            Lead.status == LeadStatus.CLOSED
        )
        last_lead_at = func.max(Lead.created_at)

        return (
            select(
                User.id,
                User.telegram_user_id,
                User.username,
                User.first_name,
                User.last_name,
                User.phone,
                total_leads.label("total_leads"),
                open_leads.label("open_leads"),
                closed_leads.label("closed_leads"),
                last_lead_at.label("last_lead_at"),
            )
            .join(Lead, Lead.user_id == User.id)
            .group_by(
                User.id,
                User.telegram_user_id,
                User.username,
                User.first_name,
                User.last_name,
                User.phone,
            )
        )

    async def list_client_summaries(
        self,
        *,
        limit: int,
        offset: int,
    ) -> list[ClientSummaryRecord]:
        """Return aggregated clients ordered by latest request."""

        statement = (
            self._client_summary_statement()
            .order_by(
                func.max(Lead.created_at).desc(),
                User.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.execute(statement)

        return [
            (
                int(row.id),
                int(row.telegram_user_id),
                row.username,
                row.first_name,
                row.last_name,
                row.phone,
                int(row.total_leads),
                int(row.open_leads),
                int(row.closed_leads),
                row.last_lead_at,
            )
            for row in result.all()
        ]

    async def get_client_summary(
        self,
        client_id: int,
    ) -> ClientSummaryRecord | None:
        """Return aggregate data for one client."""

        statement = self._client_summary_statement().where(
            User.id == client_id
        )

        row = (await self._session.execute(statement)).one_or_none()

        if row is None:
            return None

        return (
            int(row.id),
            int(row.telegram_user_id),
            row.username,
            row.first_name,
            row.last_name,
            row.phone,
            int(row.total_leads),
            int(row.open_leads),
            int(row.closed_leads),
            row.last_lead_at,
        )

    async def count_client_leads(
        self,
        client_id: int,
    ) -> int:
        """Count all requests submitted by one client."""

        statement = select(func.count(Lead.id)).where(
            Lead.user_id == client_id
        )

        count = await self._session.scalar(statement)

        return int(count or 0)

    async def list_client_leads(
        self,
        client_id: int,
        *,
        limit: int,
        offset: int,
    ) -> list[Lead]:
        """Return one page of requests submitted by a client."""

        statement = (
            select(Lead)
            .options(selectinload(Lead.user))
            .where(Lead.user_id == client_id)
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

    async def reopen(
        self,
        *,
        lead_id: int,
        admin_telegram_id: int,
    ) -> tuple[Lead | None, bool]:
        """Return a closed lead to active work."""

        statement = (
            select(Lead)
            .options(selectinload(Lead.user))
            .where(Lead.id == lead_id)
            .with_for_update()
        )

        lead = await self._session.scalar(statement)

        if lead is None:
            return None, False

        if lead.status != LeadStatus.CLOSED:
            return lead, False

        old_status = lead.status

        lead.status = LeadStatus.IN_PROGRESS
        lead.close_comment = None
        lead.closed_at = None

        history = LeadStatusHistory(
            lead_id=lead.id,
            old_status=old_status,
            new_status=LeadStatus.IN_PROGRESS,
            admin_telegram_id=admin_telegram_id,
            comment=(
                "Закрытая заявка возвращена "
                "администратором в работу"
            ),
        )

        self._session.add(history)
        await self._session.flush()

        return lead, True

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
