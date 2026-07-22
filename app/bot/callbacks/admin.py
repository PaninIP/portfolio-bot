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


class LeadAttachmentsCallback(
    CallbackData,
    prefix="lead_files",
):
    """Callback for sending one lead's stored attachments."""

    lead_id: int


class LeadDatePresetCallback(
    CallbackData,
    prefix="lead_date",
):
    """Callback for selecting a predefined date period."""

    preset: str


class LeadResultPageCallback(
    CallbackData,
    prefix="lead_result_page",
):
    """Callback for navigating search or date-filter results."""

    mode: str
    page: int


class LeadResultOpenCallback(
    CallbackData,
    prefix="lead_result_open",
):
    """Callback for opening a result without losing the result list."""

    mode: str
    lead_id: int
    page: int


class AdminInputCancelCallback(
    CallbackData,
    prefix="admin_input_cancel",
):
    """Callback for cancelling an administrator text-input flow."""

    action: str


class ClientPageCallback(
    CallbackData,
    prefix="cl_page",
):
    """Callback for navigating client-directory pages."""

    page: int


class ClientOpenCallback(
    CallbackData,
    prefix="cl_open",
):
    """Callback for opening a client card."""

    client_id: int
    page: int


class ClientLeadPageCallback(
    CallbackData,
    prefix="cl_lead_page",
):
    """Callback for navigating one client's request pages."""

    client_id: int
    clients_page: int
    page: int


class ClientLeadOpenCallback(
    CallbackData,
    prefix="cl_lead_open",
):
    """Callback for opening a request from a client card."""

    lead_id: int
    clients_page: int
    page: int
