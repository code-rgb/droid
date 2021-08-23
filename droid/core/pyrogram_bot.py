import asyncio
import signal
from abc import ABC, abstractmethod

from pyrogram import Client
from pyrogram.types import User


class PyroBot(ABC):
    client: Client
    bot_info: User
    _is_running: bool

    def __init__(self):
        super().__init__()

    async def init_bot(self):
        self.client = Client(session_name="droid", **self.config._client)
        await self.client.start()
        self.bot_info = await self.client.get_me()
        self.log.info("Pyrogram client stated.")
        self.log.info("Loading modules...")
        await self.load_modules()
        await self.register_handlers()

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
            self.log.info("Idling...")
            await self.idle()
        finally:
            await self.stop()
