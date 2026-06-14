import httpx

from ai_interface import AIModel, ModelInfo
from yandex_auth import YandexAuth

SYSTEM_PROMPT = (
    "Ты — эксперт по ремонту и дизайну интерьеров. "
    "Отвечай подробно, профессионально, давай практические советы. "
    "При генерации дизайн-проекта описывай: цветовую гамму, материалы, "
    "мебель, освещение, текстиль, декор."
)


class YandexGPTBot(AIModel):

    def __init__(self, folder_id: str, auth: YandexAuth, model: str = "yandexgpt-lite"):
        self.folder_id = folder_id
        self.auth = auth
        self.model = model

    @property
    def info(self) -> ModelInfo:
        return ModelInfo(
            id="yandexgpt",
            name="YandexGPT",
            icon="\U0001f916",
            description="Нейросеть от Яндекса",
        )

    async def _chat_completion(self, messages: list[dict]) -> str:
        headers = self.auth.get_auth_headers()
        headers["Content-Type"] = "application/json"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers=headers,
                json={
                    "modelUri": f"gpt://{self.folder_id}/{self.model}",
                    "completionOptions": {
                        "temperature": 0.6,
                        "maxTokens": 2000,
                    },
                    "messages": messages,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["result"]["alternatives"][0]["message"]["text"]

    async def chat(self, history: list[dict]) -> str:
        messages = [{"role": "system", "text": SYSTEM_PROMPT}]
        for msg in history:
            messages.append({"role": msg["role"], "text": msg["message"]})
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
            {"role": "system", "text": SYSTEM_PROMPT},
            {"role": "user", "text": prompt},
        ])

    async def repair_advice(self, question: str) -> str:
        return await self._chat_completion([
            {"role": "system", "text": SYSTEM_PROMPT},
            {"role": "user", "text": f"Вопрос по ремонту: {question}"},
        ])

    async def interior_tip(self, question: str) -> str:
        return await self._chat_completion([
            {"role": "system", "text": SYSTEM_PROMPT},
            {"role": "user", "text": f"Вопрос по интерьеру: {question}"},
        ])
