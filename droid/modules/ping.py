from .. import mod
from ..core.command_context import Ctx
from ..decor import OnCmd


class Ping(mod.Module):
    @OnCmd("pingme", admin_only=True)
    async def on_message(self, ctx: Ctx):
        await ctx.msg.reply_text("Pong !")

    # @OnCmd("clear_cache", admin_only=True)
    # async def cmd_clear_cache(self, ctx: Ctx):
    #     refresh_admin_cache(ctx.msg.chat.id)
    #     await ctx.msg.reply_text("Cached Cleared")
