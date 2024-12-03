import logging

from pydantic_settings import BaseSettings, SettingsConfigDict

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

BASE_URL = "https://auto.ria.com"


class Settings(BaseSettings):
    IS_TEST: bool = False
    MAX_PARALLEL_PIPELINE_WORKERS: int = 10
    MAX_PARALLEL_IMAGE_WORKERS: int = 10
    ASYNC_SQLITE_URL: str = "sqlite+aiosqlite:///database.sqlite"
    BOT_TOKEN: str = "7920586635:AAHC5sXYcnAICp2flh8rEBgS8BXllA0MXZk"

    model_config = SettingsConfigDict(env_file=".env", str_strip_whitespace=True, extra="ignore")


settings = Settings()  # type: ignore
