import openai

from ai_interface import AIModel, ModelInfo

SYSTEM_PROMPT = (
    "Ты — эксперт по ремонту и дизайну интерьеров. "
    "Отвечай подробно, профессионально, давай практические советы. "
    "При генерации дизайн-проекта описывай: цветовую гамму, материалы, "
    "мебель, освещение, текстиль, декор."
)


class QwenBot(AIModel):

    def __init__(self, api_key: str, folder_id: str, model: str = "qwen3.6-35b-a3b"):
        self.api_key = api_key
        self.folder_id = folder_id
        self.model = model
        self.client = openai.AsyncOpenAI(
            base_url="https://ai.api.cloud.yandex.net/v1",
            api_key=api_key,
        )

    @property
    def info(self) -> ModelInfo:
        return ModelInfo(
            id="qwen",
            name="Qwen 3.6-35B",
            icon="\U0001f9e0",
            description="Мультимодальная модель от Yandex Cloud",
        )

    async def _chat_completion(self, messages: list[dict]) -> str:
        response = await self.client.chat.completions.create(
            model=f"gpt://{self.folder_id}/{self.model}",
            messages=messages,
            temperature=0.6,
            max_tokens=4000,
        )
        return response.choices[0].message.content

    async def chat(self, history: list[dict]) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history:
            if "content" in msg:
                messages.append({"role": msg["role"], "content": msg["content"]})
            else:
                messages.append({"role": msg["role"], "content": msg.get("message") or msg.get("text", "")})
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

    async def analyze_image(self, image_bytes: bytes) -> str:
        import base64
        image_b64 = base64.b64encode(image_bytes).decode()
        prompt = (
            "Опиши это помещение для дизайн-проекта: "
            "какая комната, размер (примерно), цветовая гамма, "
            "какая мебель и предметы есть, состояние стен/пола/потолка, "
            "освещение. Коротко, 3-5 предложений."
        )
        return await self._chat_completion([
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
            ]}
        ])
