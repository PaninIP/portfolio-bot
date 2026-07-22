from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from enum import StrEnum
from math import ceil

from app.database.enums import (
    DeliveryStatus,
    LeadStatus,
    NotificationType,
)
from app.database.models.lead import Lead
from app.database.repositories import (
    LeadRepository,
    NotificationRepository,
)
from app.database.session import async_session_factory


DEFAULT_PAGE_SIZE = 5


class LeadListType(StrEnum):
    """Available administrator lead lists."""

    NEW = "new"
    ACTIVE = "active"
    ARCHIVE = "archive"


class LeadResultMode(StrEnum):
    """Available mixed-status result modes."""

    SEARCH = "search"
    DATE = "date"


@dataclass(frozen=True, slots=True)
class LeadPage:
    """One page of administrator lead results."""

    items: tuple[Lead, ...]
    list_type: LeadListType
    page: int
    total_pages: int
    total_items: int


@dataclass(frozen=True, slots=True)
class LeadResultPage:
    """One page of search or date-filter results."""

    items: tuple[Lead, ...]
    mode: LeadResultMode
    page: int
    total_pages: int
    total_items: int


@dataclass(frozen=True, slots=True)
class ClientSummary:
    """Aggregate administrator data for one Telegram client."""

    client_id: int
    telegram_user_id: int
    username: str | None
    first_name: str
    last_name: str | None
    phone: str | None
    total_leads: int
    open_leads: int
    closed_leads: int
    last_lead_at: datetime

    @property
    def display_name(self) -> str:
        """Return the client's Telegram profile name."""

        return (
            " ".join(
                part
                for part in (
                    self.first_name,
                    self.last_name,
                )
                if part
            ).strip()
            or "Пользователь Telegram"
        )


@dataclass(frozen=True, slots=True)
class ClientPage:
    """One page of the administrator client directory."""

    items: tuple[ClientSummary, ...]
    page: int
    total_pages: int
    total_items: int


@dataclass(frozen=True, slots=True)
class ClientLeadPage:
    """One page of requests submitted by a single client."""

    items: tuple[Lead, ...]
    client_id: int
    page: int
    total_pages: int
    total_items: int


@dataclass(frozen=True, slots=True)
class LeadStatusChangeResult:
    """Result of an administrator status-change operation."""

    found: bool
    changed: bool
    current_status: LeadStatus | None


@dataclass(frozen=True, slots=True)
class LeadReopenResult:
    """Result of returning a closed lead to active work."""

    found: bool
    changed: bool
    current_status: LeadStatus | None
    lead_id: int | None
    client_telegram_id: int | None


def get_list_statuses(
    list_type: LeadListType,
) -> tuple[LeadStatus, ...]:
    """Return statuses included in an administrator list."""

    if list_type == LeadListType.NEW:
        return (LeadStatus.NEW,)

    if list_type == LeadListType.ARCHIVE:
        return (LeadStatus.CLOSED,)

    return (
        LeadStatus.IN_PROGRESS,
        LeadStatus.WAITING_FOR_CLIENT,
    )


def get_lead_list_type(status: LeadStatus) -> LeadListType:
    """Return the standard administrator list for a status."""

    if status == LeadStatus.NEW:
        return LeadListType.NEW

    if status == LeadStatus.CLOSED:
        return LeadListType.ARCHIVE

    return LeadListType.ACTIVE


def _normalize_page(
    *,
    requested_page: int,
    total_items: int,
    page_size: int,
) -> tuple[int, int]:
    """Return normalized current page and total page count."""

    total_pages = max(
        1,
        ceil(total_items / page_size),
    )
    normalized_page = min(
        max(requested_page, 1),
        total_pages,
    )

    return normalized_page, total_pages


def get_utc_period(
    *,
    start_date: date,
    end_date: date,
) -> tuple[datetime, datetime]:
    """Convert inclusive calendar dates into a UTC half-open period."""

    start = datetime.combine(
        start_date,
        time.min,
        tzinfo=timezone.utc,
    )
    end_exclusive = datetime.combine(
        end_date + timedelta(days=1),
        time.min,
        tzinfo=timezone.utc,
    )

    return start, end_exclusive


async def get_lead_page(
    *,
    list_type: LeadListType,
    page: int,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> LeadPage:
    """Return one paginated lead list."""

    statuses = get_list_statuses(list_type)

    async with async_session_factory() as session:
        repository = LeadRepository(session)

        total_items = await repository.count_by_statuses(
            statuses
        )
        normalized_page, total_pages = _normalize_page(
            requested_page=page,
            total_items=total_items,
            page_size=page_size,
        )

        leads = await repository.list_by_statuses(
            statuses,
            limit=page_size,
            offset=(normalized_page - 1) * page_size,
        )

    return LeadPage(
        items=tuple(leads),
        list_type=list_type,
        page=normalized_page,
        total_pages=total_pages,
        total_items=total_items,
    )


async def get_search_result_page(
    *,
    query: str,
    page: int,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> LeadResultPage:
    """Return one paginated general-search result page."""

    async with async_session_factory() as session:
        repository = LeadRepository(session)

        total_items = await repository.count_search_results(
            query
        )
        normalized_page, total_pages = _normalize_page(
            requested_page=page,
            total_items=total_items,
            page_size=page_size,
        )

        leads = await repository.list_search_results(
            query,
            limit=page_size,
            offset=(normalized_page - 1) * page_size,
        )

    return LeadResultPage(
        items=tuple(leads),
        mode=LeadResultMode.SEARCH,
        page=normalized_page,
        total_pages=total_pages,
        total_items=total_items,
    )


async def get_date_result_page(
    *,
    start_date: date,
    end_date: date,
    page: int,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> LeadResultPage:
    """Return one paginated creation-date result page."""

    date_from, date_to = get_utc_period(
        start_date=start_date,
        end_date=end_date,
    )

    async with async_session_factory() as session:
        repository = LeadRepository(session)

        total_items = await repository.count_created_between(
            date_from=date_from,
            date_to=date_to,
        )
        normalized_page, total_pages = _normalize_page(
            requested_page=page,
            total_items=total_items,
            page_size=page_size,
        )

        leads = await repository.list_created_between(
            date_from=date_from,
            date_to=date_to,
            limit=page_size,
            offset=(normalized_page - 1) * page_size,
        )

    return LeadResultPage(
        items=tuple(leads),
        mode=LeadResultMode.DATE,
        page=normalized_page,
        total_pages=total_pages,
        total_items=total_items,
    )


def _build_client_summary(
    record: tuple[
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
    ],
) -> ClientSummary:
    """Convert a repository aggregate row to a service DTO."""

    return ClientSummary(
        client_id=record[0],
        telegram_user_id=record[1],
        username=record[2],
        first_name=record[3],
        last_name=record[4],
        phone=record[5],
        total_leads=record[6],
        open_leads=record[7],
        closed_leads=record[8],
        last_lead_at=record[9],
    )


async def get_client_page(
    *,
    page: int,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> ClientPage:
    """Return one page of clients who submitted requests."""

    async with async_session_factory() as session:
        repository = LeadRepository(session)

        total_items = await repository.count_clients_with_leads()
        normalized_page, total_pages = _normalize_page(
            requested_page=page,
            total_items=total_items,
            page_size=page_size,
        )

        records = await repository.list_client_summaries(
            limit=page_size,
            offset=(normalized_page - 1) * page_size,
        )

    return ClientPage(
        items=tuple(
            _build_client_summary(record)
            for record in records
        ),
        page=normalized_page,
        total_pages=total_pages,
        total_items=total_items,
    )


async def get_client_summary(
    client_id: int,
) -> ClientSummary | None:
    """Return aggregate administrator data for one client."""

    async with async_session_factory() as session:
        repository = LeadRepository(session)
        record = await repository.get_client_summary(
            client_id
        )

    if record is None:
        return None

    return _build_client_summary(record)


async def get_client_lead_page(
    *,
    client_id: int,
    page: int,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> ClientLeadPage:
    """Return one page of requests submitted by a client."""

    async with async_session_factory() as session:
        repository = LeadRepository(session)

        total_items = await repository.count_client_leads(
            client_id
        )
        normalized_page, total_pages = _normalize_page(
            requested_page=page,
            total_items=total_items,
            page_size=page_size,
        )

        leads = await repository.list_client_leads(
            client_id,
            limit=page_size,
            offset=(normalized_page - 1) * page_size,
        )

    return ClientLeadPage(
        items=tuple(leads),
        client_id=client_id,
        page=normalized_page,
        total_pages=total_pages,
        total_items=total_items,
    )


async def get_admin_lead(
    lead_id: int,
) -> Lead | None:
    """Return a lead for the administrator card."""

    async with async_session_factory() as session:
        repository = LeadRepository(session)

        return await repository.get_by_id_with_user(
            lead_id
        )


async def take_lead_in_progress(
    *,
    lead_id: int,
    admin_telegram_id: int,
) -> LeadStatusChangeResult:
    """Move a new lead into active work."""

    async with async_session_factory() as session:
        async with session.begin():
            repository = LeadRepository(session)

            lead, changed = await repository.change_status(
                lead_id=lead_id,
                allowed_from=(LeadStatus.NEW,),
                new_status=LeadStatus.IN_PROGRESS,
                admin_telegram_id=admin_telegram_id,
                comment=(
                    "Заявка взята администратором в работу"
                ),
            )

            if lead is None:
                return LeadStatusChangeResult(
                    found=False,
                    changed=False,
                    current_status=None,
                )

            return LeadStatusChangeResult(
                found=True,
                changed=changed,
                current_status=lead.status,
            )


async def reopen_closed_lead(
    *,
    lead_id: int,
    admin_telegram_id: int,
) -> LeadReopenResult:
    """Return a closed lead to active work."""

    async with async_session_factory() as session:
        async with session.begin():
            repository = LeadRepository(session)

            lead, changed = await repository.reopen(
                lead_id=lead_id,
                admin_telegram_id=admin_telegram_id,
            )

            if lead is None:
                return LeadReopenResult(
                    found=False,
                    changed=False,
                    current_status=None,
                    lead_id=None,
                    client_telegram_id=None,
                )

            return LeadReopenResult(
                found=True,
                changed=changed,
                current_status=lead.status,
                lead_id=lead.id,
                client_telegram_id=(
                    lead.user.telegram_user_id
                ),
            )


async def record_reopen_notification_delivery(
    *,
    lead_id: int,
    recipient_telegram_id: int,
    delivered: bool,
    error_message: str | None,
) -> None:
    """Store the result of a lead-reopening notification."""

    delivery_status = (
        DeliveryStatus.DELIVERED
        if delivered
        else DeliveryStatus.FAILED
    )

    delivered_at = (
        datetime.now(timezone.utc)
        if delivered
        else None
    )

    async with async_session_factory() as session:
        async with session.begin():
            repository = NotificationRepository(session)

            await repository.create(
                lead_id=lead_id,
                recipient_telegram_id=(
                    recipient_telegram_id
                ),
                notification_type=(
                    NotificationType.LEAD_STATUS_CHANGED
                ),
                delivery_status=delivery_status,
                error_message=error_message,
                delivered_at=delivered_at,
            )
