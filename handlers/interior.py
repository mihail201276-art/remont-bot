import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from database import get_chat_history, get_or_create_user, save_chat_message
from model_registry import ModelRegistry

logger = logging.getLogger(__name__)

router = Router()
MAX_LEN = 4000


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

    await save_chat_message(message.from_user.id, "user", message.text, model.info.id)

    try:
        history = await get_chat_history(message.from_user.id, limit=6)
        history = history[:-1]
        text = await model.chat(history)
    except Exception:
        logger.exception("Interior handler error")
        await status_msg.edit_text(
            "\u274c Ошибка. Попробуйте переключить модель через /model"
        )
        return

    await save_chat_message(message.from_user.id, "assistant", text, model.info.id)

    footer = f"\n\n\u2014\n{model.info.icon} {model.info.name}"
    max_body = MAX_LEN - len(footer)
    if len(text) > max_body:
        text = text[:max_body] + "..."
    await status_msg.edit_text(text + footer)
