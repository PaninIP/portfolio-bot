from aiogram import Router

from app.bot.handlers.admin import router as admin_router
from app.bot.handlers.lead_form import router as lead_form_router
from app.bot.handlers.main_menu import router as main_menu_router
from app.bot.handlers.start import router as start_router
from app.bot.handlers.admin_leads import (
    router as admin_leads_router,
)

def get_handlers_router() -> Router:
    """Create and return the root handlers router."""

    router = Router(name="handlers")

    router.include_router(start_router)
    router.include_router(admin_router)
    router.include_router(admin_leads_router)
    router.include_router(lead_form_router)
    router.include_router(main_menu_router)

    return router