import httpx

from ai_interface import AIModel, ModelInfo
from get_token import get_gigachat_token

SYSTEM_PROMPT = (
    "Ты — эксперт по ремонту и дизайну интерьеров. "
    "Отвечай подробно, профессионально, давай практические советы. "
    "При генерации дизайн-проекта описывай: цветовую гамму, материалы, "
    "мебель, освещение, текстиль, декор."
)


class GigaChatBot(AIModel):

    def __init__(self, credentials: str, scope: str):
        self.credentials = credentials
        self.scope = scope
        self._token_data: dict | None = None

    @property
    def info(self) -> ModelInfo:
        return ModelInfo(
            id="gigachat",
            name="GigaChat",
            icon="\U0001f9e0",
            description="Нейросеть от Сбера",
        )

    async def _ensure_token(self):
        if not self._token_data:
            self._token_data = await get_gigachat_token(self.credentials, self.scope)

    async def _chat_completion(self, messages: list[dict]) -> str:
        await self._ensure_token()
        token = self._token_data["access_token"]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "GigaChat",
                    "messages": messages,
                    "temperature": 0.6,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def chat(self, history: list[dict]) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history:
            if "content" in msg:
                messages.append({"role": msg["role"], "content": msg["content"]})
            else:
                messages.append({"role": msg["role"], "content": msg.get("text", "")})
        return await self._chat_completion(messages)

    async def generate_design(self, description: str, style: str, wishes: str | None = None) -> str:
        prompt = (
            f"На основе помещения: {description}.\n"
            f"Желаемый стиль: {style}.\n"
        )
        if wishes:
            prompt += f"Дополнительные пожелания: {wishes}.\n"
        prompt += (
            "Опиши подробный дизайн-проект: цветовая гамма, материалы, "
            "мебель, освещение, текстиль, декор."
        )
        return await self._chat_completion([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])

    async def repair_advice(self, question: str) -> str:
        return await self._chat_completion([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Вопрос по ремонту: {question}"},
        ])

    async def interior_tip(self, question: str) -> str:
        return await self._chat_completion([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Вопрос по интерьеру: {question}"},
        ])
