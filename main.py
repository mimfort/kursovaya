import asyncio

from aiogram import Bot, Dispatcher

from bot.handlers import start as start_handlers
from bot.handlers import stats as stats_handlers
from bot.handlers import tasks as task_handlers
from core.config import load_settings
from core.logging import setup_logging
from db.base import init_db


async def main() -> None:
    setup_logging()
    settings = load_settings()
    await init_db()

    bot = Bot(settings.bot_token)
    dp = Dispatcher()
    dp.include_router(start_handlers.router)
    dp.include_router(task_handlers.router)
    dp.include_router(stats_handlers.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
