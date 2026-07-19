from aiogram import Router

from app.bot.handlers.start import router as start_router


def get_handlers_router() -> Router:
    """Create and return the root handlers router."""

    router = Router(name="handlers")

    router.include_router(start_router)

    return router