from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from database import get_or_create_user
from model_registry import ModelRegistry

router = Router()


class DesignForm(StatesGroup):
    room_type = State()
    style = State()
    budget = State()
    wishes = State()


@router.message(F.text == "\U0001f3a8 Дизайн-проект")
@router.message(Command("design"))
async def start_design(message: Message, state: FSMContext):
    await state.set_state(DesignForm.room_type)
    await message.answer(
        "\U0001f3a8 <b>Создание дизайн-проекта</b>\n\n"
        "Напишите, какое это помещение? (например: гостиная 20м\u00b2, спальня, кухня, детская...)"
    )


@router.message(DesignForm.room_type)
async def process_room_type(message: Message, state: FSMContext):
    await state.update_data(room_type=message.text)
    await state.set_state(DesignForm.style)
    await message.answer(
        "Какой стиль предпочитаете?\n"
        "(лофт, минимализм, скандинавский, прованс, классика, модерн, хай-тек, свой вариант)"
    )


@router.message(DesignForm.style)
async def process_style(message: Message, state: FSMContext):
    await state.update_data(style=message.text)
    await state.set_state(DesignForm.budget)
    await message.answer(
        "Какой бюджет на ремонт/обустройство? "
        "(можно указать примерную сумму или диапазон)"
    )


@router.message(DesignForm.budget)
async def process_budget(message: Message, state: FSMContext):
    await state.update_data(budget=message.text)
    await state.set_state(DesignForm.wishes)
    await message.answer(
        "Есть ли особые пожелания? (цвета, материалы, функциональность, "
        "или напишите 'нет')"
    )


@router.message(DesignForm.wishes)
async def process_wishes(message: Message, state: FSMContext):
    data = await state.get_data()
    wishes = message.text if message.text.lower() != "нет" else ""

    status_msg = await message.answer("\u23f3 Генерирую дизайн-проект...")

    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    registry: ModelRegistry = message.bot.model_registry
    model = registry.get_model(user.current_model)

    description = (
        f"Помещение: {data['room_type']}\n"
        f"Стиль: {data['style']}\n"
        f"Бюджет: {data['budget']}\n"
    )
    if wishes:
        description += f"Пожелания: {wishes}"

    try:
        text = await model.generate_design(
            description, data["style"], wishes or None
        )
    except Exception as e:
        await status_msg.edit_text(
            f"\u274c Ошибка: {e}. Попробуйте переключить модель через /model"
        )
        await state.clear()
        return

    await state.clear()

    footer = f"\n\n\u2014\n{model.info.icon} {model.info.name}"
    await status_msg.edit_text(text + footer)
