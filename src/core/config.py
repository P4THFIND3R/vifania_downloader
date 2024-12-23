from pathlib import Path
from datetime import datetime

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_ID: int
    API_HASH: str
    SESSION_NAME: str = "my_account"

    TARGET: int = -1001989999005
    DAYS: int = 6
    LIMIT: int = 500

    CATALOG: str = "documents/Файлы"
    FILENAME_LINKS: str = "Ссылки.txt"

    @property
    def today(self):
        return datetime.now().strftime("%d.%m")

    @property
    def catalog_today(self) -> Path:
        return Path.home() / self.today

    @property
    def links_filename(self) -> Path:
        return self.catalog_today / self.FILENAME_LINKS

    class Config:
        env_file = ".env"


settings = Settings()
