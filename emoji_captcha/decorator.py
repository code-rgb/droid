from typing import List, Pattern, Union

from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineQuery, Message

from .config import botconfig
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

    @staticmethod
    def base_filter(owner_only: bool = False) -> filters.Filter:
        async def func(_, __, query):
            # Check query
            if not isinstance(query, Message):
                return False
            # Check Owner
            if owner_only and query.from_user.id != botconfig.owner_id:
                return False
            return True

        return filters.create(func)


class OnFlt(BaseDecorator):
    def __init__(self, filters: filters.Filter, group: int = 0, *args, **kwargs):
        super().__init__(
            filters=filters, group=group, handle="message", *args, **kwargs
        )


class OnCallback(BaseDecorator):
    def __init__(
        self,
        regex: Union[str, Pattern],
        group: int = 0,
        owner_only: bool = False,
        *args,
        **kwargs
    ):
        super().__init__(
            filters=(
                filters.regex(regex, kwargs.get("flags", 0))
                & self.base_filter(owner_only=owner_only)
            ),
            group=group,
            handle="callback",
            *args,
            **kwargs
        )

    @staticmethod
    def base_filter(owner_only: bool = False) -> filters.Filter:
        async def func(_, __, query):
            # Check query
            if not isinstance(query, CallbackQuery):
                return False
            # Check Owner
            if owner_only and query.from_user.id != botconfig.owner_id:
                return False
            return True

        return filters.create(func)


class OnInline(BaseDecorator):
    def __init__(
        self,
        regex: Union[str, Pattern],
        group: int = 0,
        owner_only: bool = False,
        *args,
        **kwargs
    ):
        super().__init__(
            filters=(
                filters.regex(regex, kwargs.get("flags", 0))
                & self.base_filter(owner_only=owner_only)
            ),
            group=group,
            handle="inline",
            *args,
            **kwargs
        )

    @staticmethod
    def base_filter(owner_only: bool = False) -> filters.Filter:
        async def func(_, __, query):
            # Check query
            if not isinstance(query, InlineQuery):
                return False
            # Check Owner
            if owner_only and query.from_user.id != botconfig.owner_id:
                return False
            return True

        return filters.create(func)


class OnDelete(BaseDecorator):
    # TODO
    pass
