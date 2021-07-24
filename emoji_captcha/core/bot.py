import asyncio
import logging
import time
from datetime import datetime
from typing import Optional

import aiohttp
import ujson

from ..config import Config, botconfig
from .emojipedia import EmojiCaptcha
from .loader import Loader
from .pyrogram_bot import PyroBot


class Bot(PyroBot, Loader, EmojiCaptcha):
    config: Config
    http_session: Optional[aiohttp.ClientSession]
    loop: asyncio.AbstractEventLoop
    stopped: bool
    uptime_reference: int
    log: logging.Logger

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.http_session = None
        self.config = botconfig
        self.loop = loop or asyncio.get_event_loop()
        self.log = logging.getLogger(self.__class__.__name__)
        self.start_datetime = datetime.utcnow()
        self.uptime_reference = time.monotonic_ns()
        self.stopped = False
        super().__init__()

    @property
    def __http_isactive(self) -> bool:
        return self.http_session and not self.http_session.closed

    @property
    def http(self) -> aiohttp.ClientSession:
        if not self.__http_isactive:
            self.http_session = aiohttp.ClientSession(json_serialize=ujson.dumps)
        return self.http_session

    @property
    def uptime(self):
        return time.monotonic_ns() - self.uptime_reference

    async def stop(self):
        self.log.info("Stopping bot...")
        self.stopped = True
        self.log.info("Executing on_exit tasks...")
        await self.on_exit_tasks()
        if self.__http_isactive:
            self.log.info("Closing http session...")
            await self.http_session.close()
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
