import asyncio
import re

from pyrogram import filters
from pyrogram.errors import UserAdminInvalid
from pyrogram.types import User

from .. import mod
from ..core.command_context import Ctx
from ..decor import OnFlt
from ..utils import get_media

CHAT = -1001378211961


class AntiArabic(mod.Module):
    async def on_load(self):

        # https://en.wikipedia.org/wiki/Arabic_script#endnote_arabic_alphabet
        self.ARABIC = re.compile(
            "["
            r"\u0600-\u06FF"  # Arabic
            r"\u0750-\u077F"  # Arabic Supplement
            r"\u08A0-\u08FF"  # Arabic Extended-A
            r"\uFB50-\uFDFF"  # Arabic Pres. Forms-A
            r"\uFE70-\uFEFF"  # Arabic Pres. Forms-B
            r"\u1EE0-\u1EEF"  # Arabic Mathematical...
            r"\u1EC7-\u1ECB"  # Indic Siyaq Numbers
            r"\u1ED0-\u1ED4"  # Ottoman Siyaq Numbers
            r"\u10E6-\u10E7"  # Rumi Numeral Symbols
            "]+"
        )

    @OnFlt(filters.chat(CHAT))
    async def detect(self, ctx: Ctx):

        # New Members
        if new_members := ctx.msg.new_chat_members:
            for user in new_members:
                triggers = [user.first_name or "", user.last_name or ""]
                if ub := self.bot.userbot:
                    try:
                        bio = (await ub.get_chat(user.username or user.id)).bio or ""
                    except Exception:
                        pass
                    else:
                        triggers.append(bio)
                for text in triggers:
                    if await self.check_arabic(text, user, ctx):
                        break
            return
        if ctx.msg.text:
            await self.check_arabic(ctx.msg.text, ctx.msg.from_user, ctx)
        elif ctx.msg.media and (media := get_media(ctx.msg)):
            for text in (ctx.msg.caption or "", getattr(media, "file_name", "")):
                if await self.check_arabic(text, ctx.msg.from_user, ctx):
                    break

    async def check_arabic(self, text: str, user: User, ctx: Ctx) -> bool:
        if self.ARABIC.search(text):
            try:
                await ctx.msg.chat.kick_member(user.username or user.id)
            except UserAdminInvalid:
                pass
            else:
                await asyncio.gather(
                    ctx.reply(
                        f"⛔️ Banned **{user.mention}**\nID: `{user.id}`\nReason: **Arabic**",
                        quote=False,
                        del_in=10,
                    ),
                    ctx.msg.delete(),
                )
            return True
        return False
