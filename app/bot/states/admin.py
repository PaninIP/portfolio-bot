from aiogram.fsm.state import State, StatesGroup


class LeadCloseForm(StatesGroup):
    """States used while closing a project request."""

    comment = State()
    confirmation = State()


class LeadSearchForm(StatesGroup):
    """States used while searching project requests."""

    query = State()
    results = State()


class LeadDateFilterForm(StatesGroup):
    """States used while filtering requests by creation date."""

    custom_period = State()
    results = State()