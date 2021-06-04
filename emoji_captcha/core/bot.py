import asyncio
import logging
import os
import signal
import time
from datetime import datetime
from typing import Optional

import aiohttp
import pyrogram
import ujson

from ..config import Config
from .pyrogram_bot import PyroBot
from .emojipedia import EmojiCaptcha


class Bot(PyroBot, EmojiCaptcha):
    config: "Config"
    http_session: Optional[aiohttp.ClientSession]
    loop: asyncio.AbstractEventLoop
    stopped: bool
    uptime_reference: int
    log: logging.Logger

    def __init__(self):
        self.http_session = None
        self.config = Config()
        self.loop = asyncio.get_event_loop()
        self.log = logging.getLogger(self.__class__.__name__)
        self.start_datetime = datetime.utcnow()
        self.uptime_reference = time.monotonic_ns()
        self.stopped = False
        super().__init__()

    @property
    def http(self) -> aiohttp.ClientSession:
        if self.http_session is None or self.http_session.closed:
            self.http_session = aiohttp.ClientSession(json_serialize=ujson.dumps)
        return self.http_session

    @property
    def uptime(self):
        return time.monotonic_ns() - self.uptime_reference

    async def stop(self):
        self.log.info("Stopping bot...")
        self.stopped = True
        if self.http_session and not self.http_session.closed:
            self.log.info("Closing http session...")
            await self.http_session.close()
        if self.client.is_initialized:
            await self.client.stop()
            self.log.info("Pyrogram client closed.")
        self.log.info("Bot stopped.")
        self.loop.stop()

    @classmethod
    async def begin(cls, *, loop: Optional[asyncio.AbstractEventLoop] = None) -> "Bot":
        bot = None

        if loop:
            asyncio.set_event_loop(loop)

        try:
            bot = cls()
            await bot.start()
            return bot
        finally:
            if bot is None or (bot is not None and not bot.stopped):
                asyncio.get_event_loop().stop()
