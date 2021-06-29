from typing import List, Union

from pyrogram import filters
from pyrogram.types import Message

from .config import config
from .core.base_decorator import BaseDecorator


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
            admin_only=admin_only,
            *args,
            **kwargs
        )

    def base_filter(self, owner_only: bool = False) -> filters.Filter:
        async def func(_, __, query):
            # Check query
            if not isinstance(query, Message):
                return False
            # Check Owner
            if owner_only and query.from_user.id != config.owner_id:
                return False
            return True

        return filters.create(func)

    
class OnFlt(BaseDecorator):
    def __init__(
        self,
        filters: filters.Filter,
        group: int = 0,
        *args,
        **kwargs
    ):
        super().__init__(
            filters=filters,
            group=group,
            handle="message",
            *args,
            **kwargs
        )


class OnCallback(BaseDecorator):
    #TODO
    pass


class OnInline(BaseDecorator):
    #TODO
    pass

class OnDelete(BaseDecorator):
    #TODO
    pass