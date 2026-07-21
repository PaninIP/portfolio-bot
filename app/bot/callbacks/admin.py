from aiogram.filters.callback_data import CallbackData


class LeadCloseCallback(
    CallbackData,
    prefix="lead_close",
):
    """Callback for starting lead closure."""

    lead_id: int
    list_type: str
    page: int


class LeadCloseDecisionCallback(
    CallbackData,
    prefix="lead_close_decision",
):
    """Callback for confirming or cancelling lead closure."""

    action: str
    lead_id: int
    list_type: str
    page: int


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


class LeadStatusCallback(
    CallbackData,
    prefix="lead_status",
):
    """Callback for changing a lead status."""

    lead_id: int
    target_status: str
    list_type: str
    page: int


class LeadReopenCallback(
    CallbackData,
    prefix="lead_reopen",
):
    """Callback for returning a closed lead to active work."""

    lead_id: int
    list_type: str
    page: int
