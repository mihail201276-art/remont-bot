import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

from config import Config
from database import init_db
from giga_bot import GigaChatBot
from handlers import start, help, model, photo, design, repair, interior
from model_registry import ModelRegistry
from qwen_bot import QwenBot
from yandex_art import YandexART
from yandex_auth import YandexAuth
from yandex_gpt import YandexGPTBot

logger = logging.getLogger(__name__)


async def run_bot(config: Config) -> None:
    await init_db(config)

    yandex_auth = YandexAuth(config.yandex_api_key)

    yandexgpt = YandexGPTBot(
        config.yandex_api_key, config.yandex_folder_id, config.yandexgpt_model
    )
    yandex_art = YandexART(config.yandex_folder_id, yandex_auth)

    registry = ModelRegistry()
    registry.register(yandexgpt)

    qwen = QwenBot(config.yandex_api_key, config.yandex_folder_id)
    registry.register(qwen)

    if config.gigachat_credentials and config.gigachat_credentials != "ПОКА_НЕТ":
        gigachat = GigaChatBot(config.gigachat_credentials, config.gigachat_scope)
        registry.register(gigachat)
        logger.info("GigaChat подключён")
    else:
        logger.info("GigaChat не настроен, работает только YandexGPT")

    session = None
    if config.tg_proxy:
        session = AiohttpSession(proxy=config.tg_proxy)

    bot = Bot(
        token=config.bot_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    bot.config = config
    bot.yandex_art = yandex_art
    bot.model_registry = registry

    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(help.router)
    dp.include_router(model.router)
    dp.include_router(photo.router)
    dp.include_router(design.router)
    dp.include_router(repair.router)
    dp.include_router(interior.router)

    logger.info("Бот запущен")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
