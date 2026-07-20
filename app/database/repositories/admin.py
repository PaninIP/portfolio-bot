from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.admin import AdminSettings


class AdminRepository:
    """Provide database operations for administrators."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self,
        admin_telegram_id: int,
    ) -> AdminSettings | None:
        """Return administrator settings by Telegram ID."""

        statement = select(AdminSettings).where(
            AdminSettings.admin_telegram_id == admin_telegram_id
        )

        return await self._session.scalar(statement)

    async def ensure_exists(
        self,
        admin_telegram_id: int,
    ) -> AdminSettings:
        """Create administrator settings if they do not exist."""

        statement = (
            insert(AdminSettings)
            .values(
                admin_telegram_id=admin_telegram_id,
                is_active=True,
                notifications_enabled=True,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    AdminSettings.admin_telegram_id,
                ],
            )
        )

        await self._session.execute(statement)

        admin = await self.get(admin_telegram_id)

        if admin is None:
            raise RuntimeError(
                "Failed to create administrator settings"
            )

        return admin

    async def toggle_notifications(
        self,
        admin: AdminSettings,
    ) -> bool:
        """Toggle administrator notifications."""

        admin.notifications_enabled = (
            not admin.notifications_enabled
        )

        await self._session.flush()

        return admin.notifications_enabled