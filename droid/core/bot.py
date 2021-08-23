import asyncio
import logging
import time
from datetime import datetime
from typing import Optional

from ..config import CONFIG, Config
from .http import Http
from .loader import Loader
from .pyrogram_bot import PyroBot


class Bot(Http, PyroBot, Loader):
    config: Config
    loop: asyncio.AbstractEventLoop
    stopped: bool
    uptime_reference: int
    log: logging.Logger

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.config = CONFIG
        self.loop = loop or asyncio.get_event_loop()
        self.log = logging.getLogger(self.__class__.__name__)
        self.start_datetime = datetime.utcnow()
        self.uptime_reference = time.monotonic_ns()
        self.stopped = False
        super().__init__()

    @property
    def uptime(self):
        return time.monotonic_ns() - self.uptime_reference

    async def stop(self):
        self.log.info("Stopping bot...")
        self.stopped = True
        self.log.info("Executing on_exit tasks...")
        await self.on_exit_tasks()
        self.log.info("Closing http session...")
        await self.close_session()
        if self.client.is_initialized:
            self.log.info("Stopping pyrogram client...")
            await self.client.stop()
        self.log.info("Bot stopped.")
        self.loop.stop()

    @classmethod
    async def begin(cls, *, loop: Optional[asyncio.AbstractEventLoop] = None) -> "Bot":
        bot = None

        if loop:
            asyncio.set_event_loop(loop)

        try:
            bot = cls(loop=loop)
            await bot.start()
            return bot
        finally:
            if bot is None or (bot is not None and not bot.stopped):
                asyncio.get_event_loop().stop()
