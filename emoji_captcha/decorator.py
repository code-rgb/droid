from typing import Pattern, Union, List, Dict
from pyrogram import filters
from pyrogram.methods.utilities import restart
from pyrogram.types import Message
from .core.base_decorator import BaseDecorator, Ctx
from .config import config


class OnCmd(BaseDecorator):
    def __init__(
        self,
        cmd: Union[str, List[str]],
        prefixes: Union[str, List[str]] = "/",
        case_sensitive: bool = False,
        group: int = 0,
        owner_only: bool = False,
        admin_only: bool = False,
        *args,
        **kwargs
    ):
        super().__init__(
            filters=(
                filters.command(cmd, prefixes, case_sensitive)
                & self.base_filter(owner_only=owner_only)
            ),
            group=group,
            handle="message",
            *args,
            **kwargs
        )

    def base_filter(self, owner_only: bool = False):
        async def func(_, __, query):
            # Check query
            if isinstance(query, Message):
                return False
            # Check Owner
            if owner_only and query.from_user.id != config.owner_id:
                return False
            return True

        return filters.create(func)
