import asyncio
import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from database import get_or_create_user, save_chat_message
from model_registry import ModelRegistry

logger = logging.getLogger(__name__)

router = Router()

STYLES = [
    ("loft", "Лофт"),
    ("minimalism", "Минимализм"),
    ("scandinavian", "Скандинавский"),
    ("provence", "Прованс"),
    ("classic", "Классика"),
    ("modern", "Модерн"),
    ("hi-tech", "Хай-тек"),
    ("other", "Другой"),
]


class PhotoForm(StatesGroup):
    waiting_photo = State()
    waiting_style = State()


def _style_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for i, (style_id, style_name) in enumerate(STYLES):
        row.append(
            InlineKeyboardButton(
                text=style_name, callback_data=f"photo_style:{style_id}"
            )
        )
        if len(row) == 2 or i == len(STYLES) - 1:
            buttons.append(row)
            row = []
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "\U0001f4f8 Фото комнаты")
async def start_photo_flow(message: Message, state: FSMContext):
    await state.set_state(PhotoForm.waiting_photo)
    await message.answer(
        "\U0001f4f8 <b>Опишите вашу комнату</b>\n\n"
        "Напишите коротко: размеры, планировка, текущая отделка, "
        "какая мебель есть, что хотите изменить.\n\n"
        "Например:\n"
        "<i>«Комната 4×5 м, потолок 2.7 м, одно окно, "
        "пол ламинат, стены белые, нужна спальня»</i>"
    )


@router.message(PhotoForm.waiting_photo, F.text)
async def handle_room_description(message: Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)
    await state.set_state(PhotoForm.waiting_style)
    await message.answer(
        "\U0001f3a8 <b>Выберите стиль</b> для дизайн-проекта:",
        reply_markup=_style_keyboard(),
    )


@router.message(PhotoForm.waiting_photo)
async def handle_not_photo(message: Message, state: FSMContext):
    await message.answer(
        "\U0001f4f8 Пожалуйста, опишите комнату текстом."
    )


@router.callback_query(F.data.startswith("photo_style:"))
async def cb_photo_style(callback: CallbackQuery, state: FSMContext):
    style_id = callback.data.split(":")[1]
    style_name = dict(STYLES).get(style_id, style_id)
    data = await state.get_data()

    await callback.message.edit_text(
        f"\u23f3 Генерирую дизайн-проект в стиле <b>{style_name}</b>..."
    )

    user = await get_or_create_user(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name,
    )

    registry: ModelRegistry = callback.bot.model_registry
    model = registry.get_model(user.current_model)

    room_desc = data.get("description", "помещение")

    await save_chat_message(callback.from_user.id, "user", f"Фото комнаты, стиль: {style_name}. Описание: {room_desc}", model.info.id)

    try:
        text = await model.generate_design(room_desc, style_name)
    except Exception:
        logger.exception("Photo design generation error")
        await callback.message.answer(
            "\u274c Ошибка генерации. Попробуйте переключить модель через /model"
        )
        await state.clear()
        await callback.answer()
        return

    await save_chat_message(callback.from_user.id, "assistant", text, model.info.id)

    await state.set_state(PhotoForm.waiting_style)

    footer = f"\n\n\u2014\n{model.info.icon} {model.info.name}"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\U0001f3a8 Другой стиль",
                    callback_data="photo_restyle",
                ),
                InlineKeyboardButton(
                    text="\U0001f4ac Задать вопрос", callback_data="photo_ask"
                ),
            ]
        ]
    )

    max_body = 4000 - len(footer)
    if len(text) > max_body:
        text = text[:max_body] + "..."

    await callback.message.answer(text + footer, reply_markup=kb)

    art = getattr(callback.bot, "yandex_art", None)
    if art:
        try:
            art_prompt = art.build_prompt(room_desc, style_name)
            image_bytes = await asyncio.wait_for(art.generate_image(art_prompt), timeout=20)
            if image_bytes:
                await callback.message.answer_photo(
                    photo=BufferedInputFile(image_bytes, filename="vizualization.jpg"),
                    caption=f"\U0001f3a8 Визуализация в стиле <b>{style_name}</b>",
                )
        except Exception:
            logger.exception("YandexART generation error")
    await callback.answer()


@router.callback_query(F.data == "photo_restyle")
async def cb_photo_restyle(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PhotoForm.waiting_style)
    await callback.message.edit_text(
        "\U0001f3a8 <b>Выберите новый стиль</b> для дизайн-проекта:",
        reply_markup=_style_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "photo_ask")
async def cb_photo_ask(callback: CallbackQuery):
    await callback.message.answer(
        "\U0001f4ac Задайте ваш вопрос по этому дизайн-проекту. "
        "Или используйте /repair для консультации по ремонту."
    )
    await callback.answer()
