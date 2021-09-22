from .. import mod
from ..core.command_context import Ctx
from ..decor import OnCmd
import asyncio
import json


class Ping(mod.Module):
    @OnCmd("me", admin_only=True)
    async def on_message(self, ctx: Ctx):

        await ctx.reply(str(await self.bot.client.get_me()))

    # @OnCmd("clear_cache", admin_only=True)
    # async def cmd_clear_cache(self, ctx: Ctx):
    #     refresh_admin_cache(ctx.msg.chat.id)
    #     await ctx.msg.reply_text("Cached Cleared")
