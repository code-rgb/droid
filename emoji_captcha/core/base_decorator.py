import logging
from functools import wraps
from typing import Dict, List

from pyrogram import Client, ContinuePropagation, StopPropagation, StopTransmission
from pyrogram.types import ChatMember, Message, Update

from ..mod import Module
from ..utils import format_exception
from .command_context import Ctx

_CHAT_ADMINS: Dict[int, List[ChatMember]] = {}
logger = logging.getLogger(__name__)


class BaseDecorator:
    """Base decorator class"""

    def __init__(self, *args, **kwargs):

        self.args = args
        self.kwargs = kwargs

    def _add_attributes(self, _func):
        if not hasattr(_func, "_handle"):
            for attr in ("handle", "filters", "group"):
                setattr(_func, f"_{attr}", self.kwargs.get(attr))

    def __call__(self, func):
        @wraps(func)
        async def wrapper(mod: Module, client: Client, update: Update):
            if not await self.check(client, update):
                return

            context = Ctx(update) if isinstance(update, Message) else update

            try:
                out = await func(mod, context)
            except (StopPropagation, StopTransmission, ContinuePropagation) as p_e:
                raise p_e
            except BaseException as exc:
                mod.log.error(format_exception(exc))

            else:
                return out

        self._add_attributes(wrapper)
        return wrapper

    async def check(self, c: Client, u: Update):
        if isinstance(u, Message):
            if self.kwargs.get("admin_only"):
                return await self.check_admin(u)
        return True

    async def check_admin(self, m: Message) -> bool:
        global _CHAT_ADMINS
        chat_id = m.chat.id
        user_id = m.from_user.id
        if not (admins := _CHAT_ADMINS.get(chat_id)):
            try:
                admins = await m.chat.get_members(filter="administrators")
            except Exception as e:
                logging.error(format_exception(e))
                return False
            _CHAT_ADMINS[chat_id] = admins

        for admin in admins:
            if user_id == admin.user.id:
                return True
        return False


def refresh_admin_cache(chat_id: int = 0, clear_all: bool = False) -> None:
    global _CHAT_ADMINS
    if clear_all:
        _CHAT_ADMINS.clear()
    else:
        _CHAT_ADMINS.pop(chat_id, None)
