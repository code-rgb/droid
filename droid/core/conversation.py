"""
Coversation Utils

~ Inspired by pyromod, Conversation-Pyrogram
"""
import asyncio
import logging
from asyncio.futures import Future
from collections import OrderedDict
from functools import partial
from typing import Any, Dict, Optional, Union

from pyrogram import Client
from pyrogram.filters import Filter, create
from pyrogram.handlers import CallbackQueryHandler, InlineQueryHandler, MessageHandler
from pyrogram.types import CallbackQuery, InlineQuery, Message

LOG = logging.getLogger("Conversation")
Updates = Union[Message, CallbackQuery, InlineQuery]
Handlers = Union[
    MessageHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
]


class ConversationAlreadyExists(Exception):
    pass


class Conversation:

    convo_dict: Dict[str, Union[Future, Handlers]] = {}

    def __init__(
        self,
        client: Client,
        chat_id: int,
        timeout: float = 30.0,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:

        if chat_id in self.convo_dict:
            raise ConversationAlreadyExists(f"Chat ID => {self.chat_id}")

        self.client = client
        self.chat_id = chat_id
        self.timeout = timeout
        self.loop = loop or asyncio.get_running_loop()
        self.lock = asyncio.Lock()
        self.hndlr_grp = -999

    @property
    def isactive(self) -> bool:
        """check for active Conversation"""
        return self.chat_id in self.convo_dict

    async def send(self, *args: Any, **kwargs: Any) -> Message:
        """Send message"""
        kwargs.pop("chat_id", None)
        return await self.client.send_message(self.chat_id, *args, **kwargs)

    async def listen(
        self,
        filters: Optional[Filter] = None,
        timeout: Optional[float] = None,
    ) -> Optional[Message]:
        """Wait for Message response"""
        conv_filter = create(
            lambda _, __, m: ((m.chat.id == self.chat_id) and self.isactive)
        )
        return await self.__listen(
            MessageHandler,
            ((conv_filter & filters) if filters is not None else conv_filter),
            timeout,
        )

    listen_message = listen

    async def listen_callback(
        self,
        filters: Optional[Filter] = None,
        timeout: Optional[float] = None,
    ) -> Optional[CallbackQuery]:
        """Wait for Callback response"""
        conv_filter = create(
            lambda _, __, cb: (
                True if not cb.message else (cb.message.chat.id == self.chat_id)
            )
            and self.isactive
        )
        return await self.__listen(
            CallbackQueryHandler,
            ((conv_filter & filters) if filters is not None else conv_filter),
            timeout,
        )

    async def listen_inline(
        self,
        filters: Optional[Filter] = None,
        timeout: Optional[float] = None,
    ) -> Optional[InlineQuery]:
        """Wait for Inline response"""
        conv_filter = create(lambda _, __, ___: self.isactive)
        return await self.__listen(
            InlineQueryHandler,
            ((conv_filter & filters) if filters is not None else conv_filter),
            timeout,
        )

    async def __listen(
        self, hndlr: Handlers, flt: Filter, timeout: Optional[float]
    ) -> Optional[Updates]:
        fut = self.loop.create_future()
        fut.add_done_callback(partial(self.__unregister_handler))
        conv_handler = hndlr(lambda _, u: fut.set_result(u), flt)
        await self.__register_handler(conv_handler)
        self.convo_dict[self.chat_id] = dict(handler=conv_handler, future=fut)
        try:
            return await asyncio.wait_for(fut, timeout or self.timeout)
        except asyncio.TimeoutError:
            LOG.error(
                (
                    "Ended conversation, 🕐 Timeout reached !"
                    f"\n  Chat ID => {self.chat_id}"
                    f"\n  Handler => {hndlr.__class__.__name__}"
                )
            )

    async def __register_handler(self, hndlr: Handlers) -> None:
        """Register Conversation handler"""
        dispatcher = self.client.dispatcher
        async with self.lock:
            if self.hndlr_grp not in dispatcher.groups:
                dispatcher.groups[self.hndlr_grp] = []
                dispatcher.groups = OrderedDict(sorted(dispatcher.groups.items()))
            dispatcher.groups[self.hndlr_grp].append(hndlr)

    def __unregister_handler(self, *_) -> None:
        """Unregister Conversation handler"""
        if not self.isactive:
            LOG.warning(f"No active Conversations found in Chat ID => {self.chat_id}")
            return

        async def func() -> None:
            if hndlr := self.convo_dict[self.chat_id].get("handler"):
                dispatcher = self.client.dispatcher
                async with self.lock:
                    if self.hndlr_grp not in dispatcher.groups:
                        LOG.warning(
                            f"Group {self.hndlr_grp} does not exist. Handler was not removed."
                        )
                        return
                    dispatcher.groups[self.hndlr_grp].remove(hndlr)
                self.convo_dict.pop(self.chat_id, None)

        self.loop.create_task(func())

    async def __aenter__(self) -> "Conversation":
        if not isinstance(self.chat_id, int):
            self.chat_id = (await self.client.get_chat(self.chat_id)).id
        return self

    async def __aexit__(self, *_, **__) -> None:
        self.convo_dict.pop(self.chat_id, None)
