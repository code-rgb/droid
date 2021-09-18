import asyncio
import logging

from pyrogram import filters
from pyrogram.types.messages_and_media.message import Message

from .. import mod
from ..config import CONFIG
from ..core.command_context import Ctx
from ..core.conversation import Conversation
from ..decor import OnCmd
from ..utils import run_command


class Term(mod.Module):
    async def on_load(self):
        self.lock = asyncio.Lock()
        self.tasks = set()

    @OnCmd("term", admin_only=True)
    async def term_cmd(self, ctx: Ctx):
        async with Conversation(
            client=self.bot.client, chat_id=ctx.msg.chat.id, loop=self.bot.loop
        ) as conv:
            await conv.send("🖥  **Terminal is Now Active**")
            while True:
                if code := await conv.listen(filters.user(CONFIG.owner_id)):
                    if code.text:
                        if code.text.lower().strip() == "exit":
                            async with self.lock:
                                m = await conv.send(
                                    "❌ <i>Closing all pending tasks...</i>"
                                )
                                self.kill_tasks()
                                await m.edit_text("✅  **Exited Terminal**")
                            break
                        else:
                            async with self.lock:
                                self.tasks.add(asyncio.create_task(self.terminal(code)))

    @OnCmd("tp", admin_only=True)
    async def term_tasks(self, ctx: Ctx):
        await ctx.reply(
            "**Term Tasks**"
            + (
                "\n".join(
                    map(
                        lambda x: f"• **{x.get_name()}** - `{x.cancelled()}`",
                        self.tasks,
                    )
                )
                if bool(self.tasks)
                else "`- No Active Task found`"
            )
        )

    async def terminal(self, msg: Message):
        if msg.text:
            try:
                out, err, _, proc = await run_command(msg.text, shell=True)
                if out or err:
                    text = f"<code>~$  {msg.text}</code>"
                    if out:
                        out += f"\n\n<pre>{out}</pre>"
                    if err:
                        text += f"\n\n<b>ERROR:</b> <pre>{err}</pre>"
                    await Ctx(msg).reply(
                        text,
                        parse_mode="HTML",
                    )
            except asyncio.CancelledError:
                if proc is not None:
                    logging.info(f"Process {proc.pid} has been cancelled")
                    proc.kill()
                raise

    def kill_tasks(self):
        for task in self.tasks:
            if not task.done():
                task.cancel()
        self.tasks.clear()

    async def on_exit(self):
        if self.tasks:
            self.kill_tasks()
