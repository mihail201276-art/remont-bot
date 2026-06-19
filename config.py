from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str = ""
    gigachat_credentials: str = ""
    gigachat_scope: str = "GIGACHAT_API_PERS"
    yandex_api_key: str = ""
    yandex_folder_id: str = ""
    yandex_bucket_name: str = ""
    yandex_static_key_id: str = ""
    yandex_static_key: str = ""
    yandexgpt_model: str = "yandexgpt-5.1/latest"
    tg_proxy: str = ""
    database_url: str = "sqlite+aiosqlite:///remont_bot.db"
