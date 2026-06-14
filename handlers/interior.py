from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from database import get_or_create_user
from model_registry import ModelRegistry

router = Router()


class InteriorForm(StatesGroup):
    waiting_question = State()


@router.message(F.text == "\U0001f3e0 Интерьер")
@router.message(Command("interior"))
async def start_interior(message: Message, state: FSMContext):
    await state.set_state(InteriorForm.waiting_question)
    await message.answer(
        "\U0001f3e0 <b>Советы по интерьеру</b>\n\n"
        "Задайте ваш вопрос. Я помогу с:\n"
        "\u2022 Цветовыми решениями\n"
        "\u2022 Выбором мебели\n"
        "\u2022 Освещением и текстилем\n"
        "\u2022 Стилями и трендами\n"
        "\u2022 Декором и аксессуарами\n\n"
        "Чтобы выйти, нажмите /menu"
    )


@router.message(InteriorForm.waiting_question)
async def process_interior_question(message: Message, state: FSMContext):
    if not message.text:
        return

    status_msg = await message.answer("\u23f3 Думаю...")

    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    registry: ModelRegistry = message.bot.model_registry
    model = registry.get_model(user.current_model)

    try:
        text = await model.interior_tip(message.text)
    except Exception as e:
        await status_msg.edit_text(
            f"\u274c Ошибка: {e}. Попробуйте переключить модель через /model"
        )
        return

    footer = f"\n\n\u2014\n{model.info.icon} {model.info.name}"
    await status_msg.edit_text(text + footer)
