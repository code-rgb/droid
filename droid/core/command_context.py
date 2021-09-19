import asyncio
import re
import tempfile
from typing import Dict, List, Optional, Tuple, Union

from pyrogram.errors import MessageAuthorRequired
from pyrogram.types import Message

from ..config import CONFIG

FLAGS_RE = re.compile(
    # Valid flags: https://regex101.com/r/nQ0H9S/1
    r"(?:^|\s)-{1,2}(?P<flag>[A-Za-z_]+)[=]?(?P<value>\w+|\"[\w\s'-]+\"|\'[\w\s\"-]+\')?(?:(?=$)|(?=\s))"
)


class Ctx:
    def __init__(self, message: Message) -> None:
        self.msg = message

    @property
    def flags(self) -> Optional[Dict[str, str]]:
        """Dict of raw flags without any duplicates

        Returns:
        -------
            `Optional[Dict[str, str]]`: {"flag": "value"}
        """
        if self.msg.text:
            return dict(self.flags_raw)

    @property
    def flags_raw(self) -> Optional[List[Tuple[str, str]]]:
        """List of tuple of (flag, value)

        Returns:
        -------
            `Optional[List[Tuple[str, str]]]`: [("flag", "value")]
        """
        if self.msg.text:
            return FLAGS_RE.findall(self.msg.text)

    @property
    def input(self) -> str:
        """Input str without flags

        Returns:
        -------
            `str`
        """
        return self.filtered[len(f"{CONFIG.cmd_prefix}{self.msg.command[0]} ") :]

    @property
    def input_raw(self) -> str:
        """Input str with flags

        Returns:
        -------
            `str`
        """
        if self.msg.text:
            return self.msg.text[len(f"{CONFIG.cmd_prefix}{self.msg.command[0]} ") :]

    @property
    def filtered(self) -> str:
        """Input str with command prefix but without flag

        Returns:
        -------
            `str`
        """
        return FLAGS_RE.sub("", self.msg.text) if self.msg.text else ""

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
                mode="w", delete=True, suffix=".txt"
            ) as temp:
                temp.write(text)
                temp.seek(0)  # return to start of the file
                replied = await self.msg._client.send_document(
                    chat_id=self.msg.chat.id,
                    document=temp.name,
                    thumb=None,
                    caption="<code>Output</code>",
                    parse_mode="HTML",
                    force_document=True,
                    disable_notification=False,
                    reply_to_message_id=self.msg.message_id if quote else None,
                    reply_markup=None,
                )

        else:
            replied = await self.msg.reply_text(text, *args, quote=quote, **kwargs)
        if isinstance(del_in, (int, float)) and del_in > 0:
            await asyncio.sleep(del_in)
            return bool(await replied.delete())
        return replied
