import uuid
import asyncio
from time import time
from datetime import datetime, timedelta

from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import MessageMediaType

from src.utils.logger import logger
from src.core.config import settings
from src.repositories.repository import FileRepository


class PyrogramClient:
    def __init__(self, client: Client, repository: FileRepository):
        self.app = client
        self.repository = repository

        self.semaphore = asyncio.Semaphore(settings.SEMAPHORE)
        self.semaphore_video = asyncio.Semaphore(settings.SEMAPHORE_VIDEO)

        self.start = time()
        self.map: dict[MessageMediaType: int] = {}

    def run(self):
        try:
            self.app.run(self.download_media())
            logger.info("Хорошего собрания!")
        except Exception as e:
            logger.error(f"Ошибка при загрузке медиаконтента: {e}")

    async def download_media(self):
        logger.info("Начинаем загрузку медиаконтента...")

        async with self.app:
            app = self.app

            messages = app.get_chat_history(
                chat_id=settings.TARGET,
                limit=settings.LIMIT
            )

            tasks = []
            tasks_video = []

            async for message in messages:
                if message.date < (datetime.today() - timedelta(days=settings.DAYS)):
                    break

                match message.media:
                    case MessageMediaType.VIDEO:
                        filepath = await self.process_message(
                            MessageMediaType.VIDEO,
                            message.date,
                            message.video.file_name
                        )

                        tasks_video.append(
                            self.semaphore_wrapper(
                                self._download_with_notification,
                                self.semaphore_video,
                                message,
                                filepath
                            )
                        )

                    case MessageMediaType.DOCUMENT:
                        filepath = await self.process_message(
                            MessageMediaType.DOCUMENT,
                            message.date,
                            message.document.file_name
                        )

                        tasks.append(
                            self.semaphore_wrapper(
                                self._download_with_notification,
                                self.semaphore,
                                message,
                                filepath
                            )
                        )

                    case MessageMediaType.PHOTO:
                        filepath = await self.process_message(
                            MessageMediaType.PHOTO,
                            message.date
                        )

                        tasks.append(
                            self.semaphore_wrapper(
                                self._download_with_notification,
                                self.semaphore,
                                message,
                                filepath
                            )
                        )

                    case MessageMediaType.WEB_PAGE:
                        self.repository.add_link(message.web_page.url)

                    case _:
                        msg_text = message.text
                        if msg_text:
                            if 'https' in msg_text or 'http' in msg_text:
                                logger.info(
                                    f"!! ВНИМАНИЕ !! В текстовый документ была добавлена ссылка: '{message.text}'\n"
                                    f"Необходимо вручную перейти по ней и скачать контент!")

                                self.repository.add_link(message.text)

            await asyncio.gather(*tasks)
            await asyncio.gather(*tasks_video)

            logger.info("Сохраняем ссылки в файл...")
            self.repository.save_links()
            logger.info("Очищаем временные файлы...")
            self.repository.clear_temps()

            self._logging_result()

    async def process_message(self, message: MessageMediaType, date: datetime, filename: str | None = None) -> str:
        """ Обработка сообщения, возвращает путь для скачивания. """

        map = {
            MessageMediaType.VIDEO: "ролик",
            MessageMediaType.DOCUMENT: "документ",
            MessageMediaType.PHOTO: "фотография"
        }

        logger.info(f"Найден(а) {map.get(message)}: '{filename}', "
                    f"дата отправки: {date.strftime('%d-%m-%Y %H:%M')}")

        self.map[message] = self.map.get(message, 0) + 1

        return self.repository.get_filepath(filename)

    @staticmethod
    async def _download_with_notification(message: Message, filepath: str):
        """ Скачивание файла с уведомлением. """

        for attempt in range(3):
            try:
                await message.download(filepath)
                logger.info(f"Скачивание файла '{filepath.split("\\")[-1]}' завершено.")
                await asyncio.sleep(1)

                break
            except PermissionError as e:
                if attempt < 2:
                    # logger.warning(f"Ошибка доступа к файлу {filepath}, повтор через 1 секунду...")
                    filepath = f"{filepath}.{uuid.uuid4().hex}.temp"

                    await asyncio.sleep(2)
                else:
                    logger.error(f"Скачивание файла {filepath} завершилось ошибкой: {e}")

            except Exception as e:
                if filepath.endswith('.temp'):
                    pass
                else:
                    logger.error(f"Ошибка при скачивании файла {filepath}: {e}")

    async def semaphore_wrapper(self, coro, semaphore: asyncio.Semaphore | None, *args, **kwargs):
        if not semaphore:
            semaphore = self.semaphore
        async with semaphore:
            return await coro(*args, **kwargs)

    def _logging_result(self):
        logger.info(f"\nВсего было скачано: {sum(self.map.values())} файлов.")

        for k, v in self.map.items():
            logger.info(f'\t - {k.value}: {v}')

        logger.info(f"Загрузка медиаконтента завершена за {time() - self.start:.2f} секунд.\n")
