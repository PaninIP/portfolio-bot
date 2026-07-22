from aiogram.fsm.state import State, StatesGroup


class LeadForm(StatesGroup):
    """States used while collecting a project request."""

    name_choice = State()
    custom_name = State()
    contact = State()
    project_description = State()
    required_features = State()
    deadline = State()
    budget = State()
    comment = State()
    attachments = State()
    confirmation = State()