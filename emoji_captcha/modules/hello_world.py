from pyrogram.types import Message

from .. import mod


class HelloWorld(mod.Module):

    async def on_load(self):
        self.log.info("on_load task from hello world")

    async def on_message(self, message: Message):
        await message.reply("Ping Pong!")
