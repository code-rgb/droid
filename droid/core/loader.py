import asyncio
import inspect
from typing import Dict, List

from pyrogram.handlers import (CallbackQueryHandler, DeletedMessagesHandler,
                               InlineQueryHandler, MessageHandler)

from .. import mod, modules


class Loader:
    def __init__(self):
        self.plugins: Dict = {}
        super().__init__()

    async def load_modules(self) -> None:
        for m in modules.submodules:
            for attr in dir(m):
                if attr.startswith("__"):
                    continue
                cls = getattr(m, attr, None)
                await self.__load_classmod(cls)
        await self.on_load_tasks()

    async def __load_classmod(self, cls):
        if inspect.isclass(cls) and issubclass(cls, mod.Module) and not cls.disabled:
            self.plugins[cls.__name__] = cls(self)

    async def on_load_tasks(self) -> None:
        if self.plugins:
            on_load_all: List = []
            for cls_mod in self.plugins.values():
                if not hasattr(cls_mod, "on_load"):
                    continue

                if inspect.iscoroutinefunction(cls_mod.on_load):
                    on_load_all.append(cls_mod.on_load())
            await asyncio.gather(*on_load_all)

    async def on_exit_tasks(self) -> None:
        if self.plugins:
            on_exit_all: List = []
            for cls_mod in self.plugins.values():
                if not hasattr(cls_mod, "on_exit"):
                    continue

                if inspect.iscoroutinefunction(cls_mod.on_exit):
                    on_exit_all.append(cls_mod.on_exit())

            await asyncio.gather(*on_exit_all)

    async def register_handlers(self) -> None:
        for plugin in self.plugins.values():
            for attr in dir(plugin):
                if hasattr((func := getattr(plugin, attr)), "_handle"):
                    self.log.debug(
                        f"<Registering - {func._handle} hander - {func.__name__}>"
                    )
                    if func._handle == "message":
                        handler = MessageHandler
                    elif func._handle == "inline":
                        handler = InlineQueryHandler
                    elif func._handle == "callback":
                        handler = CallbackQueryHandler
                    elif func._handle == "delete":
                        handler = DeletedMessagesHandler
                    else:
                        raise ValueError(f"[!] Invalid Handler type: {func._handle}")

                    self.client.add_handler(handler(func, func._filters), func._group)
