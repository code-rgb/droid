import asyncio
import os
import re
import tempfile
from typing import Dict, Optional, Union

from pyrogram.errors import MessageAuthorRequired
from pyrogram.types import Message

from ..config import CONFIG

FLAGS_RE = re.compile(r"(?:^|\s)-([A-Za-z]{1,10})[=]?([A-Za-z0-9]{1,10})?(?=$|\s)")


class Ctx:
    def __init__(self, message: Message) -> None:
        self.msg = message

    @property
    def flags(self) -> Optional[Dict[str, str]]:
        if self.msg.text:
            return dict(FLAGS_RE.findall(self.msg.text))

    @property
    def input(self) -> str:
        return self.filtered[len(f"/{self.msg.command[0]} ") :]

    @property
    def input_raw(self) -> str:
        if self.msg.text:
            return self.msg.text[len(f"/{self.msg.command[0]} ") :]

    @property
    def filtered(self) -> str:
        return FLAGS_RE.sub(self.msg.text, "") if self.msg.text else ""

    async def edit(
        self, text: str, *args, del_in: float = 0.0, **kwargs
    ) -> Union[bool, Message]:
        try:
            edited = await self.msg.edit_text(text, *args, **kwargs)
        except MessageAuthorRequired:
            edited = await self.reply(text, *args, **kwargs)
        if isinstance(del_in, (int, float)) and del_in > 0:
            await asyncio.sleep(del_in)
            return bool(await edited.delete())
        return edited

    async def err(self, text: str, *args, **kwargs) -> Union[bool, Message]:
        return await self.edit(f"**ERROR**: `{text}`", *args, **kwargs)

    async def reply(
        self, text: str, *args, quote: bool = True, del_in: float = 0.0, **kwargs
    ) -> Union[bool, Message]:
        if len(text) >= CONFIG.max_text_length:
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".txt"
            ) as temp:
                f_name = temp.name
                temp.write(text)
            try:
                replied = await self.msg._client.send_document(
                    chat_id=self.msg.chat.id,
                    document=f_name,
                    thumb=None,
                    caption="<code>Output</code>",
                    parse_mode="HTML",
                    force_document=True,
                    disable_notification=False,
                    reply_to_message_id=self.msg.message_id if quote else None,
                    reply_markup=None,
                )
            finally:
                if os.path.isfile(f_name):
                    os.remove(f_name)

        else:
            replied = await self.msg.reply_text(text, *args, quote=quote, **kwargs)
        if isinstance(del_in, (int, float)) and del_in > 0:
            await asyncio.sleep(del_in)
            return bool(await replied.delete())
        return replied
