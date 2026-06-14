from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from database import get_or_create_user
from image_service import ImageService
from model_registry import ModelRegistry

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
        "\U0001f4f8 Отправьте фото вашей комнаты, и я проанализирую её "
        "и предложу дизайн-проект!"
    )


@router.message(PhotoForm.waiting_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    status_msg = await message.answer("\u23f3 Анализирую помещение...")
    file_id = message.photo[-1].file_id

    try:
        image_service: ImageService = message.bot.image_service
        result = await image_service.process_room_photo(message.bot, file_id)
    except Exception as e:
        await status_msg.edit_text(
            "\u274c Не удалось проанализировать фото. Попробуйте ещё раз."
        )
        await state.clear()
        return

    await state.update_data(
        photo_url=result["photo_url"],
        vision_description=result["description"],
    )
    await state.set_state(PhotoForm.waiting_style)

    text = (
        "\U0001f4f8 <b>Анализ помещения:</b>\n"
        f"{result['description']}\n\n"
        "\U0001f3a8 <b>Выберите стиль</b> для дизайн-проекта:"
    )
    await status_msg.edit_text(text, reply_markup=_style_keyboard())


@router.message(PhotoForm.waiting_photo)
async def handle_not_photo(message: Message, state: FSMContext):
    await message.answer(
        "\U0001f4f8 Пожалуйста, отправьте фотографию комнаты (не текст)."
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

    try:
        text = await model.generate_design(
            data.get("vision_description", "помещение"), style_name
        )
    except Exception as e:
        await callback.message.answer(
            f"\u274c Ошибка генерации: {e}. Попробуйте переключить модель через /model"
        )
        await state.clear()
        await callback.answer()
        return

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

    await callback.message.answer(text + footer, reply_markup=kb)
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
