from aiogram.fsm.state import State, StatesGroup


class LeadCloseForm(StatesGroup):
    """States used while closing a lead."""

    comment = State()
    confirmation = State()