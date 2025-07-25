import os
import uuid
import webbrowser
from pathlib import Path

from src.core.config import settings
from src.utils.logger import logger


class FileRepository:
    def __init__(self):
        self._root_path = Path.home()
        self.path: Path = self._root_path / settings.CATALOG / settings.today

        self.links: list[str] = []
        self.links_filename = self.path / settings.FILENAME_LINKS

        self.create_today_directory()

    def create_today_directory(self) -> None:
        self.path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Создан сегодняшний каталог: {self.path}")

    def open_today_directory(self) -> None:
        try:
            logger.info(f"Открыт каталог: {self.path}")
            self.path.open()
        except FileNotFoundError:
            logger.error(f"Каталог '{self.path}' не найден.")

    def get_filepath(self, path: str | None) -> str:
        path = self.clear_windows_symbols(path) if path else path

        if path:
            return self.path.joinpath(path).__str__()
        return self.path.joinpath(uuid.uuid4().__str__()[:5] + '.png').__str__()

    @staticmethod
    def clear_windows_symbols(filepath: str) -> str:
        forbidden = set('/*:|"<>\n')
        path = ''.join(s for s in filepath if s not in forbidden)
        return path

    def add_link(self, link: str):
        if link:
            try:
                webbrowser.open(link)
                logger.info(f"В браузере была открыта страница: {link}")
            except Exception as e:
                self.links.append(link)
                logger.error(f"Не удалось открыть веб-страницу: {link}, {e}")

    def save_links(self):
        if self.links:
            logger.info("Сохраняем ссылки в файл...")

            with open(self.links_filename, 'w') as file:
                for link in self.links:
                    file.write(f"{link}\n")

            logger.info(f"Ссылки сохранены в файл: {self.links_filename}")
            os.startfile(self.links_filename)

    def clear_temps(self):
        logger.info("Очищаем временные файлы...")

        for file in self.path.glob('*'):
            if file.is_file() and file.suffix == '.temp':
                file.unlink(missing_ok=True)
