from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import Config
from models import Base, ChatHistory, User

engine = None
async_session = None


async def init_db(config: Config):
    global engine, async_session
    engine = create_async_engine(config.database_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_or_create_user(
    telegram_id: int, username: str | None = None, first_name: str | None = None
) -> User:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            if username is not None:
                user.username = username
            if first_name is not None:
                user.first_name = first_name
            user.last_active = datetime.utcnow()
            await session.commit()
        return user


async def set_user_model(telegram_id: int, model_id: str):
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(current_model=model_id, last_active=datetime.utcnow())
        )
        await session.commit()


async def save_chat_message(telegram_id: int, role: str, text: str, model_used: str | None = None):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return
        msg = ChatHistory(
            user_id=user.id,
            role=role,
            model_used=model_used,
            message_text=text,
        )
        session.add(msg)
        await session.commit()


async def get_chat_history(telegram_id: int, limit: int = 10) -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return []
        rows = await session.execute(
            select(ChatHistory)
            .where(ChatHistory.user_id == user.id)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
        )
        messages = []
        for row in reversed(list(rows.scalars())):
            messages.append({"role": row.role, "content": row.message_text})
        return messages
