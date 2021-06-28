import asyncio
import inspect
from abc import ABC
from typing import Dict

from pyrogram import filters
from pyrogram.handlers import MessageHandler

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
                    lambda x: func() if ((func := getattr(x, "on_load", None)) and inspect
                                         .iscoroutinefunction(func)) else None,
                    self.plugins.values(),
                ),
            )
            await asyncio.gather(*on_load_tasks)

    async def register_handlers(self):
        for i in self.plugins.values():
            if hasattr(i, "on_message") and hasattr(
                (func := i.on_message), "__wrapped__"):
                print("added handler")
                regex = func._kwargs.get("regex")
                group = func._kwargs.get("group")
                self.client.add_handler(MessageHandler(func, filters.command(regex)),
                                        group)

            # def on_command(self, cmd, group: int = 0):
            #     def decorator(func: Callable) -> Callable:
            #         self.client.add_handler(MessageHandler(
            #             func, filters.command(cmd)), group)
            #         return func
            #     return decorator
