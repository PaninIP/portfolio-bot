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
    """Show information about the developer."""

    await message.answer(
        "<b>Обо мне</b>\n\n"
        "Я Panini — разработчик Telegram-ботов.\n\n"
        "Разрабатываю Telegram-ботов под задачи бизнеса "
        "и частных специалистов: от приёма заявок и "
        "автоматизации общения с клиентами до "
        "административных панелей, хранения данных "
        "и других индивидуальных сценариев.\n\n"
        "При разработке уделяю внимание удобству "
        "использования, понятному интерфейсу, надёжному "
        "хранению данных и возможности дальнейшего "
        "развития проекта.\n\n"
        "Этот бот — действующий пример моей работы.",
        parse_mode="HTML",
    )


@router.message(F.text == SERVICES_BUTTON)
async def handle_services(message: Message) -> None:
    """Show currently available development services."""

    await message.answer(
        "<b>Что я могу реализовать</b>\n\n"
        "• разработку Telegram-бота под ваши задачи;\n"
        "• формы заявок, анкеты и регистрацию пользователей;\n"
        "• личные кабинеты и административные панели;\n"
        "• приём фотографий, документов, видео, аудио "
        "и голосовых сообщений;\n"
        "• хранение данных в PostgreSQL;\n"
        "• поиск, фильтрацию, архивы и работу "
        "с клиентской базой;\n"
        "• уведомления и автоматизацию рабочих процессов;\n"
        "• развёртывание проекта на VPS "
        "с использованием Docker.\n\n"
        "Функциональность бота определяется требованиями "
        "конкретного проекта.",
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
            "<b>Panini — Telegram-бот для приёма "
            "и сопровождения клиентских заявок</b>\n\n"
            "Вы сейчас используете этот проект. "
            "На изображении показаны его основные возможности.\n\n"
            "<b>Задача проекта</b>\n"
            "Создать Telegram-бота, который знакомит клиента "
            "с услугами, собирает структурированную заявку "
            "и помогает администратору сопровождать обращение "
            "от получения до закрытия.\n\n"
            "<b>Возможности для клиента</b>\n"
            "• пошаговая форма заявки;\n"
            "• передача контакта Telegram;\n"
            "• указание задачи, срока и бюджета;\n"
            "• отправка документов, фотографий, видео, "
            "аудио и голосовых сообщений;\n"
            "• проверка заявки перед отправкой.\n\n"
            "<b>Возможности администратора</b>\n"
            "• новые, активные и закрытые заявки;\n"
            "• поиск, фильтрация, архив и каталог клиентов;\n"
            "• изменение статусов и связь с клиентом;\n"
            "• просмотр вложений;\n"
            "• управление уведомлениями.\n\n"
            "<b>Технологии</b>\n"
            "Python, aiogram, PostgreSQL, SQLAlchemy, Alembic, "
            "Docker Compose и VPS. Данные сохраняются "
            "в PostgreSQL, для базы настроены резервные копии."
        ),
        parse_mode="HTML",
    )