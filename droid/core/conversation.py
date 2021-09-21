__all__ = ["Conversation", "ConversationAlreadyExists"]

"""
Coversation Utils

~ Inspired by pyromod, Conversation-Pyrogram
"""
import asyncio
import logging
from asyncio.futures import Future
from collections import OrderedDict
from functools import partial
from typing import Dict, List, Optional, Union

import pyrogram
from pyrogram import Client
from pyrogram.filters import Filter, create
from pyrogram.handlers import CallbackQueryHandler, InlineQueryHandler, MessageHandler
from pyrogram.types import CallbackQuery, InlineQuery, Message

# logger
log = logging.getLogger("Conversation")

# Types
Updates = Union[Message, CallbackQuery, InlineQuery]
Handlers = Union[
    MessageHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
]

# Error


class ConversationAlreadyExists(Exception):
    pass


# Main Class
class Conversation:

    convo_dict: Dict[str, Union[Future, Handlers]] = {}

    def __init__(
        self,
        client: Client,
        chat_id: int,
        timeout: float = 30.0,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Initiate a conversation

        Parameters:
        ----------
            - client (`Client`): Pyrogram Client.
            - chat_id (`int`): Chat ID of the chat to start conversation in.
            - timeout (`float`, optional): Response wait time. (Defaults to `30.0`)
            - loop (`Optional[asyncio.AbstractEventLoop]`, optional): Current event loop (Defaults to `None`)

        Raises:
        ------
            `ConversationAlreadyExists`: In case of existing conv. in the same chat.
        """

        if chat_id in self.convo_dict:
            raise ConversationAlreadyExists(f"Chat ID => {chat_id}")

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

    async def send(
        self,
        text: str,
        parse_mode: Optional[str] = object,
        entities: List["pyrogram.types.MessageEntity"] = None,
        disable_web_page_preview: bool = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        schedule_date: int = None,
        reply_markup: Union[
            "pyrogram.types.InlineKeyboardMarkup",
            "pyrogram.types.ReplyKeyboardMarkup",
            "pyrogram.types.ReplyKeyboardRemove",
            "pyrogram.types.ForceReply",
        ] = None,
        del_in: float = 0.0,
    ) -> Message:
        """Send text messages to the chat with active Conversation.

        Parameters:
        ----------
            - text (`str`): Text of the message to be sent.
            - parse_mode (`Optional[str]`, optional):
                By default, texts are parsed using both Markdown and HTML styles)
                You can combine both syntaxes together.
                Pass "markdown" or "md" to enable Markdown-style parsing only.
                Pass "html" to enable HTML-style parsing only.
                Pass None to completely disable style parsing. (Default to `object`)
            - entities (`List[`, optional):
                List of special entities that appear in message text, which can be specified instead of *parse_mode*.
                (Defaults to `None`)
            - disable_web_page_preview (`bool`, optional): Disables link previews for links in this message.
                (Defaults to `None`)
            - disable_notification (`bool`, optional): Sends the message silently.
                Users will receive a notification with no sound. (Defaults to `None`)
            - reply_to_message_id (`int`, optional): If the message is a reply, ID of the original message.
                (Defaults to `None`)
            - schedule_date (`int`, optional): Date when the message will be automatically sent. Unix time.
                (Defaults to `None`)
            - reply_markup (`Union[
                    "pyrogram.types.InlineKeyboardMarkup",
                    "pyrogram.types.ReplyKeyboardMarkup",
                    "pyrogram.types.ReplyKeyboardRemove",
                    "pyrogram.types.ForceReply"
                ]`, optional):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user. (Defaults to `None`)
            - del_in (`float`, optional): message delete time in sec. (Defaults to `0.0`)

        Returns:
        -------
            `Message`: ~pyrogram.types.Message
        """

        msg = await self.client.send_message(
            chat_id=self.chat_id,
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup,
        )

        if isinstance(del_in, (int, float)) and del_in > 0:
            await asyncio.sleep(del_in)
            await msg.delete()
        return msg

    async def listen(
        self,
        filters: Optional[Filter] = None,
        timeout: Optional[float] = None,
    ) -> Optional[Message]:
        """Wait for Message response

        Parameters:
        ----------
            - filters (`Optional[Filter]`, optional): Pass one or more filters to allow only a subset
                of messages to be passed in your callback function. (Defaults to `None`)
            - timeout (`Optional[float]`, optional): Response wait time. (Defaults to `self.timeout`)

        Returns:
        -------
            `Optional[Message]`: On Success
        """
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
        """Wait for Callback response

        Parameters:
        ----------
            - filters (`Optional[Filter]`, optional): Pass one or more filters to allow only a subset
                of messages to be passed in your callback function. (Defaults to `None`)
            - timeout (`Optional[float]`, optional): Response wait time. (Defaults to `None`)

        Returns:
        -------
            `Optional[CallbackQuery]`: On Success
        """
        conv_filter = create(
            lambda _, __, cb: (not cb.message or (cb.message.chat.id == self.chat_id))
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
        """Wait for Inline response

        Parameters:
        ----------
            - filters (`Optional[Filter]`, optional): Pass one or more filters to allow only a subset
                of messages to be passed in your callback function. (Defaults to `None`)
            - timeout (`Optional[float]`, optional): Response wait time. (Defaults to `None`)

        Returns:
        -------
            `Optional[InlineQuery]`: On Success
        """
        conv_filter = create(lambda _, __, ___: self.isactive)
        return await self.__listen(
            InlineQueryHandler,
            ((conv_filter & filters) if filters is not None else conv_filter),
            timeout,
        )

    async def __listen(
        self, hndlr: Handlers, flt: Filter, timeout: Optional[float]
    ) -> Optional[Updates]:
        """Listen for handlers

        Parameters:
        ----------
            - hndlr (`Handlers`): The handler to be registered.
            - flt (`Filter`): Pass one or more filters to allow only a subset
                of messages to be passed in your callback function.
            - timeout (`Optional[float]`): Response wait time. (Defaults to `self.timeout`)

        Returns:
        -------
            `Optional[Updates]`: On Success
        """
        fut = self.loop.create_future()
        fut.add_done_callback(partial(self.__unregister_handler))
        conv_handler = hndlr(lambda _, u: fut.set_result(u), flt)
        await self.__register_handler(conv_handler)
        self.convo_dict[self.chat_id] = dict(handler=conv_handler, future=fut)
        try:
            return await asyncio.wait_for(fut, timeout or self.timeout)
        except asyncio.TimeoutError:
            log.error(
                (
                    "Ended conversation, 🕐 Timeout reached !"
                    f"\n  Chat ID => {self.chat_id}"
                    f"\n  Handler => {hndlr.__name__}"
                )
            )
        finally:
            if not fut.done():
                fut.cancel()

    async def __register_handler(self, hndlr: Handlers) -> None:
        """Register Conversation handler

        Parameters:
        ----------
            - hndlr (`Handlers`): The handler to be registered.
        """
        dispatcher = self.client.dispatcher
        async with self.lock:
            if self.hndlr_grp not in dispatcher.groups:
                dispatcher.groups[self.hndlr_grp] = []
                dispatcher.groups = OrderedDict(sorted(dispatcher.groups.items()))
            dispatcher.groups[self.hndlr_grp].append(hndlr)

    def __unregister_handler(self, *_) -> None:
        """Unregister Conversation handler"""
        if not self.isactive:
            log.warning(f"No active Conversations found in Chat ID => {self.chat_id}")
            return

        async def func() -> None:
            if hndlr := self.convo_dict[self.chat_id].get("handler"):
                dispatcher = self.client.dispatcher
                async with self.lock:
                    if self.hndlr_grp not in dispatcher.groups:
                        log.warning(
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
