import asyncio
import os
import signal
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

import aiohttp
import pyrogram
import ujson

from ..config import Config


class PyroBot(ABC):
    client: pyrogram.Client
    bot_info: pyrogram.types.User
    _is_running: bool

    def __init__(self):
        super().__init__()

    async def init_bot(self):
        self.client = pyrogram.Client(session_name=":memory:", **self.config._client)
        await self.client.start()
        self.bot_info = await self.client.get_me()
        self.log.info("Pyrogram client stated.")

    async def idle(self) -> None:
        signals = {
            k: v
            for v, k in signal.__dict__.items()
            if v.startswith("SIG") and not v.startswith("SIG_")
        }

        def signal_handler(signum, __):

            self.log.info(f"Stop signal received ('{signals[signum]}').")
            self._is_running = False

        for name in (signal.SIGINT, signal.SIGTERM, signal.SIGABRT):
            signal.signal(name, signal_handler)

        self._is_running = True

        while self._is_running:
            await asyncio.sleep(1)

    @abstractmethod
    async def stop(self) -> None:
        pass

    async def start(self) -> None:
        try:
            await self.init_bot()
            await self.emoji_load()
            self.log.info("Idling...")
            await self.idle()
        finally:
            await self.stop()
