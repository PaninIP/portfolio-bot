from dataclasses import dataclass
from enum import StrEnum
from math import ceil

from app.database.enums import LeadStatus
from app.database.models.lead import Lead
from app.database.repositories import LeadRepository
from app.database.session import async_session_factory


DEFAULT_PAGE_SIZE = 5


class LeadListType(StrEnum):
    """Available administrator lead lists."""

    NEW = "new"
    ACTIVE = "active"


@dataclass(frozen=True, slots=True)
class LeadPage:
    """One page of administrator lead results."""

    items: tuple[Lead, ...]
    list_type: LeadListType
    page: int
    total_pages: int
    total_items: int


@dataclass(frozen=True, slots=True)
class LeadStatusChangeResult:
    """Result of an administrator status-change operation."""

    found: bool
    changed: bool
    current_status: LeadStatus | None


def get_list_statuses(
    list_type: LeadListType,
) -> tuple[LeadStatus, ...]:
    """Return statuses included in an administrator list."""

    if list_type == LeadListType.NEW:
        return (LeadStatus.NEW,)

    return (
        LeadStatus.IN_PROGRESS,
        LeadStatus.WAITING_FOR_CLIENT,
    )


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

        total_pages = max(
            1,
            ceil(total_items / page_size),
        )

        normalized_page = min(
            max(page, 1),
            total_pages,
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