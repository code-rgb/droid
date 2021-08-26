from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultPhoto,
)
import asyncio
from .. import mod
from ..core.conversation import Conversation
from ..decor import OnCmd


class Calculator(mod.Module):
    @OnCmd("add")
    async def on_message(self, ctx):
        async with Conversation(
            client=self.bot.client, chat_id=ctx.msg.chat.id, loop=self.bot.loop
        ) as conv:
            ques = await conv.send("**Send me a number to add. Press 'q' to EXIT**")
            sum = 0
            while True:
                if reply := await conv.listen(
                    filters.create(
                        lambda _, __, m: m.text and m.text.strip().isdigit()
                    ),
                    timeout=60,
                ):
                    num = int(reply.text)
                    await conv.send(f"**>** `{sum}` + `{num}`\n\nAns. `{sum + num}`")
                    sum += num
                else:
                    await conv.send("⏰ Times UP")
                    break
