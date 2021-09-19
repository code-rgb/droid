import asyncio
import logging

from pyrogram import filters
from pyrogram.types import Message

from .. import mod
from ..config import CONFIG
from ..core.command_context import Ctx
from ..core.conversation import Conversation
from ..decor import OnCmd
from ..utils import run_command
import getpass


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
                if code := await conv.listen(
                    filters.create(
                        lambda _, __, m: m.from_user.id == CONFIG.owner_id
                        and m.text
                        and not m.text.startswith(CONFIG.cmd_prefix)
                    ),
                    timeout=300,
                ):
                    if code.text.lower().strip() in ("exit", "quit"):
                        async with self.lock:
                            m = await conv.send(
                                "❌ <i>Stopping all pending tasks...</i>"
                            )
                            self.kill()
                            await m.edit_text("✅  **Exited Terminal**")
                        break
                    else:
                        async with self.lock:
                            self.tasks.add(asyncio.create_task(self.terminal(code)))
                else:
                    await conv.send("Times Up !: Exiting Terminal...", del_in=5)
                    break

    @OnCmd("tproc", admin_only=True)
    async def term_tasks(self, ctx: Ctx):
        await ctx.reply(
            "**TASK - IS RUNNING**\n\n"
            + (
                "\n".join(
                    map(
                        lambda x: f"• **{x.get_name()}** - `{x.cancelled()}`",
                        self.tasks,
                    )
                )
                if bool(self.tasks)
                else "`No Active Task found`"
            )
        )

    @OnCmd("tkill", admin_only=True)
    async def term_kill(self, ctx: Ctx):
        if not self.tasks:
            await ctx.reply("`No Active Task found`")
            return
        if "all" in ctx.flags:
            m = await ctx.reply("❌ <i>Stopping all pending tasks...</i>")
            async with self.lock:
                self.kill()
            await m.edit_text("✅  **Done**")
        else:
            if task_name := ctx.input.split()[0]:
                for t in self.tasks:
                    if task_name == t.get_name():
                        if not t.done():
                            t.cancel()
                        async with self.lock:
                            self.tasks.remove(t)
                        await ctx.reply("✅  **Done**")
                        break
                else:
                    await ctx.reply(f"⚠️  **Not Task found with name '{task_name}'**")

    async def terminal(self, msg: Message):
        if msg.text:
            try:
                out, err, _, proc = await run_command(msg.text, shell=True)
                if out or err:
                    text = f"<code>{getpass.getuser()} ~ {msg.text}</code>"
                    if out:
                        text += f"\n<pre>{out}</pre>"
                    if err:
                        text += f"\n\n<b>ERROR:</b> <pre>{err}</pre>"
                    await Ctx(msg).reply(
                        text,
                        parse_mode="HTML",
                    )
            except asyncio.CancelledError:
                if proc is not None:
                    logging.info(f"Process ({proc.pid}) has been cancelled")
                    proc.kill()

    def kill(self):
        for task in self.tasks:
            if not task.done():
                task.cancel()
        self.tasks.clear()

    async def on_exit(self):
        if self.tasks:
            self.kill()
