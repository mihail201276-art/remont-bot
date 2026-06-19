from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from database import get_or_create_user, set_user_model
from model_registry import ModelRegistry

router = Router()


def _model_keyboard(registry: ModelRegistry, current: str) -> InlineKeyboardMarkup:
    buttons = []
    for m in registry.list_models():
        label = f"{'✅ ' if m.id == current else ''}{m.icon} {m.name}"
        buttons.append(
            [InlineKeyboardButton(text=label, callback_data=f"set_model:{m.id}")]
        )
    if not registry.get("gigachat"):
        label = "🚫 GigaChat (скоро)"
        buttons.append(
            [InlineKeyboardButton(text=label, callback_data="set_model:gigachat_pending")]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("model"))
@router.message(F.text == "\U0001f916 Модель")
async def cmd_model(message: Message, state: FSMContext):
    await state.clear()
    registry: ModelRegistry = message.bot.model_registry
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )
    current = user.current_model
    model_info = registry.get_model(current).info
    text = (
        f"\U0001f9e0 Текущая модель: <b>{model_info.icon} {model_info.name}</b>\n"
        f"({model_info.description})\n\n"
        "Выбери модель для ответов:"
    )
    await message.answer(
        text,
        reply_markup=_model_keyboard(registry, current),
    )


@router.callback_query(F.data.startswith("set_model:"))
async def cb_set_model(callback: CallbackQuery):
    model_id = callback.data.split(":")[1]
    registry: ModelRegistry = callback.bot.model_registry

    if model_id == "gigachat_pending":
        await callback.answer("GigaChat пока не подключён. API-ключ появится позже.", show_alert=True)
        return

    await set_user_model(callback.from_user.id, model_id)

    model_info = registry.get_model(model_id).info
    text = f"✅ Модель переключена на {model_info.icon} <b>{model_info.name}</b>"

    await callback.message.edit_text(
        f"{text}\n\nВыбери модель для ответов:",
        reply_markup=_model_keyboard(registry, model_id),
    )
    await callback.answer(f"Выбрана модель: {model_info.name}")
