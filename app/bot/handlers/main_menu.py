from aiogram import F, Router
from aiogram.types import FSInputFile, Message

from app.bot.keyboards.main_menu import (
    ABOUT_BUTTON,
    PORTFOLIO_BUTTON,
    SERVICES_BUTTON,
)


router = Router(name=__name__)


@router.message(F.text == ABOUT_BUTTON)
async def handle_about(message: Message) -> None:
    """Show factual information about the developer."""

    await message.answer(
        "<b>Обо мне</b>\n\n"
        "Я Panini — разработчик Telegram-ботов.\n\n"
        "Сейчас я специализируюсь на ботах-визитках "
        "и системах сбора клиентских заявок. Продумываю "
        "пользовательский сценарий, создаю формы, работу "
        "с вложениями, административные панели и хранение "
        "данных.\n\n"
        "Готовый проект разворачиваю на сервере с помощью "
        "Docker. Этот бот — действующий пример моей работы.",
        parse_mode="HTML",
    )


@router.message(F.text == SERVICES_BUTTON)
async def handle_services(message: Message) -> None:
    """Show currently available development services."""

    await message.answer(
        "<b>Что я могу реализовать</b>\n\n"
        "• Telegram-бота-визитку для специалиста или "
        "небольшой компании;\n"
        "• пошаговую форму заявки или анкеты;\n"
        "• сбор имени, контакта, описания задачи, срока "
        "и бюджета;\n"
        "• приём фотографий, документов, видео, аудио "
        "и голосовых сообщений;\n"
        "• уведомления о новых заявках;\n"
        "• административную панель со статусами заявок;\n"
        "• поиск, фильтрацию, архив и каталог клиентов;\n"
        "• хранение данных в PostgreSQL;\n"
        "• запуск проекта на VPS с использованием Docker.\n\n"
        "Состав функций определяется задачами конкретного "
        "проекта.",
        parse_mode="HTML",
    )


@router.message(F.text == PORTFOLIO_BUTTON)
async def handle_portfolio(message: Message) -> None:
    """Show the current portfolio case with its presentation."""

    portfolio_image = FSInputFile(
        "assets/portfolio/panini-case.png"
    )

    await message.answer_photo(
        photo=portfolio_image,
        caption=(
            "<b>Panini — Telegram-бот для сбора "
            "клиентских заявок</b>\n\n"
            "Вы сейчас находитесь внутри работающего проекта.\n\n"
            "<b>Задача проекта</b>\n"
            "Создать бота-визитку, который знакомит клиента "
            "с услугами, собирает структурированную заявку "
            "и помогает администратору сопровождать обращение "
            "от получения до закрытия.\n\n"
            "<b>Для клиента</b>\n"
            "• пошаговая форма заявки;\n"
            "• передача контакта Telegram;\n"
            "• указание задачи, срока и бюджета;\n"
            "• отправка документов, фото, видео и аудио;\n"
            "• проверка заявки перед отправкой.\n\n"
            "<b>Для администратора</b>\n"
            "• новые, активные и закрытые заявки;\n"
            "• поиск, фильтры, архив и каталог клиентов;\n"
            "• изменение статусов и связь с клиентом;\n"
            "• просмотр вложений и управление уведомлениями.\n\n"
            "<b>Технологии</b>\n"
            "Python, aiogram, PostgreSQL, SQLAlchemy, Alembic, "
            "Docker Compose и VPS. Для базы настроены "
            "резервные копии."
        ),
        parse_mode="HTML",
    )
