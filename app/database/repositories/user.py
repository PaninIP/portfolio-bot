from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User


class UserRepository:
    """Provide database operations for Telegram users."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        telegram_user_id: int,
        username: str | None,
        first_name: str,
        last_name: str | None,
        phone: str | None,
    ) -> User:
        """Create a user or update their current Telegram data."""

        statement = (
            insert(User)
            .values(
                telegram_user_id=telegram_user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
            )
            .on_conflict_do_update(
                index_elements=[User.telegram_user_id],
                set_={
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone": phone,
                    "updated_at": func.now(),
                },
            )
            .returning(User)
        )

        result = await self._session.scalars(statement)

        return result.one()