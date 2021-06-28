from .. import mod
from ..core.base_decorator import refresh_admin_cache
from ..core.command_context import Ctx
from ..decorator import OnCmd


class Ping(mod.Module):

    # async def on_load(self):
    #     self.log.info("on_load task from ping")

    @OnCmd("pingme", admin_only=True)
    async def on_message(self, ctx: Ctx):
        await ctx.msg.reply_text("pong")

    @OnCmd("clear_cache", admin_only=True)
    async def cmd_clear_cache(self, ctx: Ctx):
        refresh_admin_cache(ctx.msg.chat.id)
        await ctx.msg.reply_text("Cached Cleared")
