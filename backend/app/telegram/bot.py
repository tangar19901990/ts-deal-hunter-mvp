"""
Telegram bot for managing saved searches.

Runs as a long-polling background task inside the same process as the
FastAPI app (see main.py's startup event) — simplest possible setup for
an MVP on a single free-tier web service, no separate worker needed.

Commands:
    /start          - welcome + usage
    /watch <query>  - create a saved search (see commands.py for syntax)
    /list           - list this chat's saved searches
    /delete <n>     - deactivate saved search number n (from /list)
"""

import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models.saved_search import SavedSearch
from app.telegram.commands import format_saved_search, parse_watch_command

logger = logging.getLogger(__name__)

dp = Dispatcher()

WELCOME_TEXT = (
    "Привіт! Я TS Deal Hunter бот.\n\n"
    "Команди:\n"
    "/watch <товар> [max:ціна] [min:ціна] [marketplace:ebay] [condition:new] "
    "— зберегти пошук\n"
    "/list — показати збережені пошуки\n"
    "/delete <номер> — видалити пошук за номером зі списку"
)


@dp.message(Command("start"))
async def handle_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT)


@dp.message(Command("watch"))
async def handle_watch(message: Message) -> None:
    text = message.text or ""
    body = text.removeprefix("/watch").strip()

    if not body:
        await message.answer("Використання: /watch RTX 4090 max:1200")
        return

    query, filters = parse_watch_command(body)
    if not query:
        await message.answer("Не вдалося розпізнати назву товару. Спробуй: /watch RTX 4090")
        return

    async with AsyncSessionLocal() as session:
        saved_search = SavedSearch(
            telegram_chat_id=str(message.chat.id),
            query=query,
            filters=filters,
        )
        session.add(saved_search)
        await session.commit()

    filter_summary = ", ".join(f"{k}={v}" for k, v in filters.items()) or "без фільтрів"
    await message.answer(f'Збережено: "{query}" ({filter_summary})')


@dp.message(Command("list"))
async def handle_list(message: Message) -> None:
    chat_id = str(message.chat.id)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(SavedSearch)
            .where(SavedSearch.telegram_chat_id == chat_id, SavedSearch.is_active.is_(True))
            .order_by(SavedSearch.created_at)
        )
        searches = result.scalars().all()

    if not searches:
        await message.answer("У тебе ще немає збережених пошуків. Додай через /watch.")
        return

    lines = [
        format_saved_search(i + 1, s.query, s.filters) for i, s in enumerate(searches)
    ]
    await message.answer("\n".join(lines))


@dp.message(Command("delete"))
async def handle_delete(message: Message) -> None:
    text = message.text or ""
    arg = text.removeprefix("/delete").strip()

    if not arg.isdigit():
        await message.answer("Використання: /delete <номер> (номер зі списку /list)")
        return

    index = int(arg)
    chat_id = str(message.chat.id)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(SavedSearch)
            .where(SavedSearch.telegram_chat_id == chat_id, SavedSearch.is_active.is_(True))
            .order_by(SavedSearch.created_at)
        )
        searches = result.scalars().all()

        if not (1 <= index <= len(searches)):
            await message.answer(f"Немає пошуку під номером {index}. Перевір /list.")
            return

        target = searches[index - 1]
        target.is_active = False
        await session.commit()

    await message.answer(f'Видалено: "{target.query}"')


async def start_bot_polling() -> None:
    """Entry point called from main.py's startup event as a background task."""
    settings = get_settings()
    if not settings.telegram_bot_token:
        logger.info("TELEGRAM_BOT_TOKEN not set — Telegram bot disabled.")
        return

    bot = Bot(token=settings.telegram_bot_token)
    logger.info("Starting Telegram bot polling...")
    await dp.start_polling(bot)
