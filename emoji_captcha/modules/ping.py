from pyrogram import Client
from pyrogram.types import Message

from ..decorator import OnCmd
from .. import mod


class Ping(mod.Module):

    async def on_load(self):
        self.log.info("on_load task from ping")

    @OnCmd("bot_info", filter_owner=True)
    async def on_message(self, client: Client, message: Message):
        await message.reply_text(f"<pre>{self.bot.bot_info}</pre>")
