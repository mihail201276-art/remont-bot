from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

router = Router()


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="\U0001f4f8 Фото комнаты"),
                KeyboardButton(text="\U0001f3a8 Дизайн-проект"),
            ],
            [
                KeyboardButton(text="\U0001f527 Ремонт"),
                KeyboardButton(text="\U0001f3e0 Интерьер"),
            ],
            [
                KeyboardButton(text="\U0001f916 Модель"),
            ],
        ],
        resize_keyboard=True,
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! \U0001f44b Я — умный помощник по ремонту и дизайну интерьеров.\n\n"
        "\U0001f4f8 Загрузи фото комнаты — я подберу дизайн-проект\n"
        "\U0001f3a8 Опиши помещение — я создам дизайн-проект по тексту\n"
        "\U0001f527 Задай вопрос по ремонту\n"
        "\U0001f3e0 Получи совет по интерьеру\n\n"
        "Выбери действие в меню \u2193",
        reply_markup=main_keyboard(),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Главное меню:", reply_markup=main_keyboard()
    )
