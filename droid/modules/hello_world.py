import asyncio


from pyrogram import filters

from .. import mod
from ..core.conversation import Conversation
from ..decor import OnCmd


class HelloItayki(mod.Module):
    @OnCmd("start_conv", owner_only=True)
    async def on_message(self, ctx):
        async with Conversation(
            self.bot.client, ctx.msg.chat.id, loop=self.bot.loop
        ) as conv:
            await conv.send("@itayki  What is your Name ??")
            try:
                ans = await conv.listen()
            except asyncio.TimeoutError:
                await conv.send("🕛 Times up !! Samurai")
            else:
                await conv.send(f"OH NOOOO '{ans.text}' 😭😭😭😭")
