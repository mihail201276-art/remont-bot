from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ai_interface import AIModel
from models import DesignProject


class DesignService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_and_save(
        self,
        model: AIModel,
        user_id: int,
        room_id: int | None,
        description: str,
        style: str,
        wishes: str | None = None,
    ) -> tuple[str, DesignProject]:
        prompt = (
            f"Помещение: {description}\n"
            f"Стиль: {style}\n"
        )
        if wishes:
            prompt += f"Пожелания: {wishes}\n"
        prompt += "Опиши подробный дизайн-проект."

        response_text = await model.generate_design(description, style, wishes)

        project = DesignProject(
            room_id=room_id,
            user_id=user_id,
            model_used=model.info.id,
            prompt=prompt,
            response=response_text,
        )
        self.session.add(project)
        await self.session.flush()

        return response_text, project

    async def list_user_projects(self, user_id: int) -> list[DesignProject]:
        result = await self.session.execute(
            select(DesignProject)
            .where(DesignProject.user_id == user_id)
            .order_by(DesignProject.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_project(self, project_id: int) -> DesignProject | None:
        result = await self.session.execute(
            select(DesignProject).where(DesignProject.id == project_id)
        )
        return result.scalar_one_or_none()
