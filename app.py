import asyncio
import logging

from fastapi import FastAPI

from config import Config
from telegram_giga_bot import run_bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Remont Bot API")
bot_task = None
config = Config()


@app.on_event("startup")
async def startup():
    global bot_task
    logger.info("Запуск бота...")

    async def bot_wrapper():
        try:
            await run_bot(config)
        except Exception as e:
            logger.error(f"Бот остановлен с ошибкой: {e}")

    bot_task = asyncio.create_task(bot_wrapper())
    logger.info("Бот запущен в фоновом режиме")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "bot_alive": bot_task is not None and not bot_task.done(),
    }
