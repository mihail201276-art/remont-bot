from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database import async_session
from models import ChatHistory, User
from sqlalchemy import delete, select

router = Router()


@router.message(Command("clear"))
async def cmd_clear(message: Message, state: FSMContext):
    await state.clear()
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            await session.execute(
                delete(ChatHistory).where(ChatHistory.user_id == user.id)
            )
            await session.commit()
    await message.answer("\U0001f9f9 История диалога очищена.")
