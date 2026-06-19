import asyncio
import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, Message

from database import get_chat_history, get_or_create_user, save_chat_message
from model_registry import ModelRegistry

logger = logging.getLogger(__name__)

router = Router()
MAX_LEN = 4000


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
    wishes = message.text if message.text.strip().lower() not in ("нет", "нет.", "no", "нема", "не") else ""

    description = (
        f"Помещение: {data['room_type']}\n"
        f"Стиль: {data['style']}\n"
        f"Бюджет: {data['budget']}\n"
    )
    if wishes:
        description += f"Пожелания: {wishes}"

    status_msg = await message.answer("\u23f3 Генерирую дизайн-проект...")

    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    registry: ModelRegistry = message.bot.model_registry
    model = registry.get_model(user.current_model)
    style_name = data["style"]

    await save_chat_message(message.from_user.id, "user", description, model.info.id)

    try:
        text = await model.generate_design(description, style_name, wishes or None)
    except Exception:
        logger.exception("Design generation error")
        await status_msg.edit_text(
            "\u274c Ошибка. Попробуйте переключить модель через /model"
        )
        await state.clear()
        return

    await save_chat_message(message.from_user.id, "assistant", text, model.info.id)
    await state.clear()

    footer = f"\n\n\u2014\n{model.info.icon} {model.info.name}"
    max_body = MAX_LEN - len(footer)
    if len(text) > max_body:
        text = text[:max_body] + "..."
    await status_msg.edit_text(text + footer)

    art = getattr(message.bot, "yandex_art", None)
    if art:
        try:
            art_prompt = art.build_prompt(description, style_name)
            image_bytes = await asyncio.wait_for(art.generate_image(art_prompt), timeout=20)
            if image_bytes:
                await message.answer_photo(
                    photo=BufferedInputFile(image_bytes, filename="vizualization.jpg"),
                    caption=f"\U0001f3a8 Визуализация в стиле <b>{style_name}</b>",
                )
        except Exception:
            logger.exception("YandexART generation error")
