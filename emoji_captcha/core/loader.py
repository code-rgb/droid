import asyncio
import inspect
from abc import ABC
from typing import Dict

from pyrogram.handlers import CallbackQueryHandler, InlineQueryHandler, MessageHandler

from .. import mod, modules


class Loader(ABC):

    def __init__(self):
        self.plugins: Dict = {}
        super().__init__()

    async def load_modules(self):
        for m in modules.submodules:
            for attr in dir(m):
                if attr.startswith("__"):
                    continue
                cls = getattr(m, attr, None)
                await self.__load_classmod(cls)
        await self.__init_classmod()

    async def __load_classmod(self, cls):
        if inspect.isclass(cls) and issubclass(cls, mod.Module) and not cls.disabled:
            self.plugins[cls.__name__] = cls(self)

    async def __init_classmod(self):
        if self.plugins:
            on_load_tasks = filter(
                None,
                map(
                    lambda x: func() if ((func := getattr(x, "on_load", None)) and
                                         inspect.iscoroutinefunction(func)) else None,
                    self.plugins.values(),
                ),
            )
            await asyncio.gather(*on_load_tasks)

    async def register_handlers(self):
        for plugin in self.plugins.values():
            for attr in dir(plugin):
                if hasattr((func := getattr(plugin, attr)), "_handle"):
                    self.log.debug(f"<registering {func._handle} hander for {func.__name__}>")
                    if func._handle == "message":
                        handler = MessageHandler
                    elif func._handle == "inline":
                        handler = InlineQueryHandler
                    elif func._handle == "callback":
                        handler = CallbackQueryHandler
                    else:
                        raise ValueError(f"Invalid Handler type: {func._handle}")

                    self.client.add_handler(handler(func, func._filters),
                                            func._priority)
