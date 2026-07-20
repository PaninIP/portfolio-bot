from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from app.services.admin_service import (
    activate_admin,
    has_admin_access,
)


class IsAdmin(Filter):
    """Allow updates only from an active administrator."""

    async def __call__(
        self,
        event: Message | CallbackQuery,
    ) -> bool:
        user = event.from_user

        if user is None:
            return False

        if await has_admin_access(user.id):
            return True

        return await activate_admin(user.id)