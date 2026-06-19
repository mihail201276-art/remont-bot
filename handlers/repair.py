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


class RepairForm(StatesGroup):
    waiting_question = State()


@router.message(F.text == "\U0001f527 Ремонт")
@router.message(Command("repair"))
async def start_repair(message: Message, state: FSMContext):
    await state.set_state(RepairForm.waiting_question)
    await message.answer(
        "\U0001f527 <b>Консультация по ремонту</b>\n\n"
        "Задайте ваш вопрос. Я помогу с:\n"
        "\u2022 Выбором материалов\n"
        "\u2022 Планировкой и зонированием\n"
        "\u2022 Бюджетом и сметой\n"
        "\u2022 Этапами работ\n"
        "\u2022 Сантехникой, электрикой, отделкой\n\n"
        "Чтобы выйти, нажмите /menu"
    )


@router.message(RepairForm.waiting_question)
async def process_repair_question(message: Message, state: FSMContext):
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
        logger.exception("Repair handler error")
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
