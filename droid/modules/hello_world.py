from .. import mod
from ..decor import OnCmd


class HelloWorld(mod.Module):
    @OnCmd("hello")
    async def on_message(self, ctx):
        await ctx.msg.reply_text("HI !")
