from pyrogram import Client
from pyrogram.types import Message

from .. import mod
from ..decorator import OnCmd, Ctx


class Ping(mod.Module):
    async def on_load(self):
        self.log.info("on_load task from ping")

    @OnCmd("pingme")
    async def on_message(self, ctx: Ctx):
        await ctx.msg.reply_text("pong")
