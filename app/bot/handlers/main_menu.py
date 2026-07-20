from aiogram import F, Router
from aiogram.types import Message

from app.bot.keyboards.main_menu import (
    ABOUT_BUTTON,
    DISCUSS_PROJECT_BUTTON,
    PORTFOLIO_BUTTON,
    SERVICES_BUTTON,
)


router = Router(name=__name__)


@router.message(F.text == ABOUT_BUTTON)
async def handle_about(message: Message) -> None:
    """Show information about the developer."""

    await message.answer(
        "Я Panini.\n\n"
        "Я разрабатываю Telegram-ботов для автоматизации бизнес-процессов, "
        "сбора заявок, взаимодействия с клиентами и интеграции внешних сервисов.\n\n"
        "В работе я уделяю внимание структуре проекта, безопасности данных "
        "и возможности дальнейшего развития продукта."
    )


@router.message(F.text == SERVICES_BUTTON)
async def handle_services(message: Message) -> None:
    """Show available development services."""

    await message.answer(
        "Основные направления разработки:\n\n"
        "• боты для сбора заявок;\n"
        "• боты-визитки;\n"
        "• запись и бронирование;\n"
        "• уведомления и рассылки;\n"
        "• интеграции с CRM, таблицами и внешними API;\n"
        "• приём файлов и формирование документов;\n"
        "• административные панели."
    )


@router.message(F.text == PORTFOLIO_BUTTON)
async def handle_portfolio(message: Message) -> None:
    """Show portfolio information."""

    await message.answer(
        "Раздел с примерами работ пока формируется.\n\n"
        "Здесь будут размещены описания проектов, используемые технологии "
        "и результаты автоматизации."
    )
