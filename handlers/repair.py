from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from database import get_or_create_user
from model_registry import ModelRegistry

router = Router()


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

    try:
        text = await model.repair_advice(message.text)
    except Exception as e:
        await status_msg.edit_text(
            f"\u274c Ошибка: {e}. Попробуйте переключить модель через /model"
        )
        return

    footer = f"\n\n\u2014\n{model.info.icon} {model.info.name}"
    await status_msg.edit_text(text + footer)
