from typing import Dict, Optional, Union
from pyrogram.types import Message
from pyrogram.errors import MessageAuthorRequired
import re
import asyncio

FLAGS_RE = re.compile(r"(?:^|\s)-([A-Za-z]{1,10})[=]?([A-Za-z0-9]{1,10})?(?=$|\s)")


class Ctx:
    def __init__(self, message: Message) -> None:
        self.msg = message

    @property
    def flags(self) -> Optional[Dict[str, str]]:
        if self.msg.text:
            return dict(FLAGS_RE.findall(self.msg.text))

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
        self, *args, quote: bool = True, del_in: float = 0.0, **kwargs
    ) -> Union[bool, Message]:
        replied = await self.msg.reply_text(*args, quote=quote, **kwargs)
        if isinstance(del_in, (int, float)) and del_in > 0:
            await asyncio.sleep(del_in)
            return bool(await replied.delete())
        return replied
