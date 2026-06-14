import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import Config
from database import init_db
from giga_bot import GigaChatBot
from handlers import start, help, model, photo, design, repair, interior
from image_service import ImageService
from model_registry import ModelRegistry
from yandex_auth import YandexAuth
from yandex_gpt import YandexGPTBot
from yandex_vision import YandexVision

logger = logging.getLogger(__name__)


async def run_bot(config: Config) -> None:
    await init_db(config)

    yandex_auth = YandexAuth(config.yandex_api_key)
    yandex_vision = YandexVision(config.yandex_folder_id, yandex_auth)

    image_service = ImageService(config, yandex_vision)

    gigachat = GigaChatBot(config.gigachat_credentials, config.gigachat_scope)
    yandexgpt = YandexGPTBot(
        config.yandex_folder_id, yandex_auth, config.yandexgpt_model
    )

    registry = ModelRegistry()
    registry.register(gigachat)
    registry.register(yandexgpt)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    bot.config = config
    bot.image_service = image_service
    bot.yandex_vision = yandex_vision
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
