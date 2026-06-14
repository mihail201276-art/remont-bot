from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "\U0001f916 Как пользоваться ботом:\n\n"
        "\U0001f4f8 <b>Фото комнаты</b> — загрузи фото, я проанализирую и предложу дизайн\n"
        "\U0001f3a8 <b>Дизайн-проект</b> — опиши помещение текстом, я создам проект\n"
        "\U0001f527 <b>Ремонт</b> — задай вопрос по ремонту, материалам, бюджету\n"
        "\U0001f3e0 <b>Интерьер</b> — получи советы по стилю, цветам, мебели\n"
        "\U0001f916 <b>Модель</b> — переключи между GigaChat и YandexGPT\n\n"
        "Команды:\n"
        "/start — главное меню\n"
        "/help — эта справка\n"
        "/model — выбор модели"
    )
    await message.answer(text)
