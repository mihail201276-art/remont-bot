class YandexAuth:

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_auth_headers(self) -> dict:
        return {"Authorization": f"Api-Key {self.api_key}"}
