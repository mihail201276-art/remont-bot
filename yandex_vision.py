import base64

import httpx

from yandex_auth import YandexAuth


class YandexVision:

    def __init__(self, folder_id: str, auth: YandexAuth):
        self.folder_id = folder_id
        self.auth = auth

    async def analyze_image(self, image_bytes: bytes) -> str:
        headers = self.auth.get_auth_headers()
        headers["Content-Type"] = "application/json"
        image_b64 = base64.b64encode(image_bytes).decode()

        body = {
            "folderId": self.folder_id,
            "analyzeSpecs": [
                {
                    "content": image_b64,
                    "features": [
                        {"type": "OBJECT_DETECTION"},
                        {"type": "CLASSIFICATION"},
                    ],
                }
            ],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://vision.api.cloud.yandex.net/vision/v3/batchAnalyze",
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            data = response.json()

        descriptions = []
        for result in data.get("results", []):
            for category in result.get("objectDetection", {}).get("objects", []):
                descriptions.append(category.get("name", ""))
            results_array = (
                result.get("results", [])
                or result.get("classification", {}).get("properties", [])
            )
            if isinstance(results_array, list):
                for item in results_array:
                    name = item.get("name", "")
                    if name:
                        descriptions.append(name)

        return ", ".join(descriptions) if descriptions else "помещение"
