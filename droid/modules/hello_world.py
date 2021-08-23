from .. import mod
from ..decor import OnCmd


class HelloWorld(mod.Module):
    async def on_load(self):
        self.attrx = "ok"
        self.log.info("on_load task from hello world")

    @OnCmd("hello")
    async def on_message(self, ctx):
        await ctx.msg.reply_text(self.attrx)
