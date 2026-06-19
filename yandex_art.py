import asyncio
import base64
import logging
from io import BytesIO

import httpx

from yandex_auth import YandexAuth

logger = logging.getLogger(__name__)


class YandexART:

    def __init__(self, folder_id: str, auth: YandexAuth):
        self.folder_id = folder_id
        self.auth = auth
        self._model_uri = f"art://{folder_id}/yandex-art/latest"

    async def generate_image(self, prompt: str, timeout: int = 15) -> bytes | None:
        headers = self.auth.get_auth_headers()
        headers["Content-Type"] = "application/json"

        body = {
            "modelUri": self._model_uri,
            "messages": [{"weight": "1", "text": prompt}],
            "generationOptions": {
                "aspectRatio": {"widthRatio": "1", "heightRatio": "1"},
                "seed": hash(prompt) % (2**31),
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync",
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            operation_id = response.json()["id"]

            for attempt in range(timeout // 3):
                await asyncio.sleep(3)
                status_resp = await client.get(
                    f"https://llm.api.cloud.yandex.net/operations/{operation_id}",
                    headers=headers,
                )
                status_resp.raise_for_status()
                data = status_resp.json()
                if data.get("done"):
                    image_b64 = data["response"]["image"]
                    return base64.b64decode(image_b64)

            logger.warning(f"YandexART timeout for operation {operation_id}")
            return None

    @staticmethod
    def build_prompt(description: str, style: str) -> str:
        return (
            f"Интерьер помещения. Стиль: {style}. "
            f"Описание: {description}. "
            "Фотореалистичное изображение, высокое качество, "
            "профессиональный дизайн интерьера."
        )
