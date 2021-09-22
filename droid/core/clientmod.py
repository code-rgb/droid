import asyncio
from logging import getLogger

from pyrogram import Client
from pyrogram.errors import FloodWait, SlowmodeWait

log = getLogger(__name__)


class Droid(Client):
    def __init__(self, *args, **kwargs):
        self.__max_tries: int = 5
        super().__init__(*args, **kwargs)

    async def send(self, *args, **kwargs):
        try_count = 0

        while True:
            try:
                return await super().send(*args, **kwargs)
            except (FloodWait, SlowmodeWait) as e:
                if try_count > self.__max_tries:
                    raise e
                log.info(f"{e.__class__.__name__}: sleeping for - {e.x}s.")
                await asyncio.sleep(e.x + 2)
                try_count += 1
