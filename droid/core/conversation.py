"""
Coversation Utils

~ Inspired by pyromod, Conversation-Pyrogram
"""
from asyncio.futures import Future
import asyncio
import logging
from collections import OrderedDict
from functools import partial
from typing import Any, Dict, Optional, Union

from pyrogram import Client
from pyrogram.filters import Filter, create
from pyrogram.handlers import MessageHandler, handler
from pyrogram.types import Message

LOG = logging.getLogger(__name__)


class ConversationAlreadyExists(Exception):
    pass


class Conversation:
    convo_dict: Dict[str, Union[Future, handler.Handler]] = {}

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
        ignore_errors: bool = False,
    ):
        """Wait for Conversation response"""
        fut = self.loop.create_future()
        fut.add_done_callback(partial(self.__unregister))
        await self.__register(filters, fut)
        try:
            return await asyncio.wait_for(fut, timeout or self.timeout)
        except asyncio.TimeoutError as e:
            if not ignore_errors:
                raise e
            LOG.error("Ended conversation, timeout reached !")

    async def __register(self, filters: Filter, fut: Future) -> None:
        """Register Conversation handler"""

        async def conv_response(_, message: Message) -> None:
            fut.set_result(message)

        conv_filter = create(
            lambda _, __, m: ((m.chat.id == self.chat_id) and self.isactive)
        )

        hndlr = MessageHandler(
            conv_response,
            filters=(conv_filter & filters) if filters is not None else conv_filter,
        )
        self.convo_dict[self.chat_id] = dict(handler=hndlr, future=fut)
        dispatcher = self.client.dispatcher
        async with self.lock:
            if self.hndlr_grp not in dispatcher.groups:
                dispatcher.groups[self.hndlr_grp] = []
                dispatcher.groups = OrderedDict(sorted(dispatcher.groups.items()))
            dispatcher.groups[self.hndlr_grp].append(hndlr)

    def __unregister(self, *_) -> None:
        """Unregister Conversation handler for chat"""
        if not self.isactive:
            LOG.warning("No active Conversations found")
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
