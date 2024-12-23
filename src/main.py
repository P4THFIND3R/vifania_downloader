from pyrogram import Client

from src.core.config import settings
from src.services.telegram import PyrogramClient
from src.repositories.repository import FileRepository


def main():
    app = Client(
        name=settings.SESSION_NAME,
        api_id=settings.API_ID,
        api_hash=settings.API_HASH
    )
    repository = FileRepository()

    client = PyrogramClient(app, repository)
    client.run()


if __name__ == '__main__':
    main()
