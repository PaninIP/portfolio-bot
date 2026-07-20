from aiogram.filters.callback_data import CallbackData


class LeadPageCallback(
    CallbackData,
    prefix="lead_page",
):
    """Callback for navigating lead-list pages."""

    list_type: str
    page: int


class LeadOpenCallback(
    CallbackData,
    prefix="lead_open",
):
    """Callback for opening a lead card."""

    lead_id: int
    list_type: str
    page: int