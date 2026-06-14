import uuid
from base64 import b64encode

import httpx


async def get_gigachat_token(credentials: str, scope: str) -> dict:
    auth_header = b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_header}",
        "RqUID": str(uuid.uuid4()),
        "Content-Type": "application/x-www-form-urlencoded",
    }

    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
            headers=headers,
            data={"scope": scope},
        )
        response.raise_for_status()
        return response.json()
