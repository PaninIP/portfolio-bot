from aiogram import F, Router
from aiogram.types import Message

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
    """Show the current portfolio case."""

    await message.answer(
        "<b>Panini — бот для сбора и обработки заявок</b>\n\n"
        "Вы сейчас находитесь внутри этого проекта.\n\n"
        "<b>Задача</b>\n"
        "Создать Telegram-бота, через которого клиент может "
        "ознакомиться с услугами и отправить структурированную "
        "заявку.\n\n"
        "<b>Пользовательская часть</b>\n"
        "• пошаговое заполнение заявки;\n"
        "• передача контакта Telegram;\n"
        "• описание проекта, срок и бюджет;\n"
        "• комментарии и вложения;\n"
        "• предварительный просмотр перед отправкой.\n\n"
        "<b>Административная часть</b>\n"
        "• новые, активные и закрытые заявки;\n"
        "• карточки клиентов и история обращений;\n"
        "• поиск, фильтрация и архив;\n"
        "• изменение статусов и управление уведомлениями;\n"
        "• повторный просмотр сохранённых вложений.\n\n"
        "<b>Техническая часть</b>\n"
        "Python, aiogram, PostgreSQL, SQLAlchemy, Alembic, "
        "Docker Compose и VPS. Данные сохраняются после "
        "перезапуска, для базы настроены резервные копии.",
        parse_mode="HTML",
    )
