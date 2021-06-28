import traceback
from functools import wraps
from typing import Dict, List

from pyrogram import Client
from pyrogram.types import ChatMember, Message

from ..mod import Module
from .command_context import Ctx

CHAT_ADMINS: Dict[int, List[ChatMember]]


class BaseDecorator:
    """Base decorator class"""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def _add_attr(self, _func):
        if not hasattr(_func, "_handle"):
            setattr(_func, "_handle", self.kwargs.get("handle", "message"))
            setattr(_func, "_filters", self.kwargs.get("filters"))
            setattr(_func, "_priority", self.kwargs.get("group", 0))

    def __call__(self, func):

        @wraps(func)
        async def wrapper(mod: Module, client: Client, message: Message):

            if not await self.check(client, message):
                return

            try:
                out = await func(mod, Ctx(message))
            except Exception as exc:
                mod.log.error("".join(
                    traceback.format_exception(etype=type(exc),
                                               value=exc,
                                               tb=exc.__traceback__)))
            else:
                return out

        self._add_attr(wrapper)
        return wrapper

    async def check(self, c: Client, m: Message):
        if self.kwargs.get("admin_only"):
            return await self.check_admin(c, m)
        return True

    async def check_admin(self, c: Client, m: Message):
        global CHAT_ADMINS
        chat_id = m.chat.id
        if not (admins := CHAT_ADMINS.get(chat_id)):
            try:
                admins = await c.get_chat_members(chat_id, filter="administrators")
            except Exception:
                admins = []
            CHAT_ADMINS[chat_id] = admins
        return m.from_user.id in list(map(lambda x: x.user.id, admins))
