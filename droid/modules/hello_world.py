from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .. import mod
from ..core.conversation import Conversation
from ..decor import OnCmd


class HelloItayki(mod.Module):
    @OnCmd("cbtest", admin_only=True)
    async def on_message(self, ctx):
        async with Conversation(
            client=self.bot.client, chat_id=ctx.msg.chat.id, loop=self.bot.loop
        ) as conv:
            await conv.send(
                "@itayki  Click this button !",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🌖🌗🌘 <PRESS> 🌒🌓🌔", callback_data="click_me"
                            )
                        ]
                    ]
                ),
            )
            if c_q := await conv.listen_callback(filters.regex(r"click_me")):
                await c_q.answer("✅ SUCCESS")
                await conv.send(f"Wowww button was clicked 😭😭😭😭")
                await c_q.edit_message_text("🌝🌞 ITS WORKING AAAAAAAAAAAAA")
            else:
                await conv.send("🕛 Times up !! Samurai")
            msg = await conv.send("ok now reply to this message")
            if reply := await conv.listen(
                filters.create(
                    lambda _, __, m: (r := m.reply_to_message)
                    and r.message_id == msg.message_id
                )
            ):
                await reply.reply_text(f"cool !!, you replied with {reply.text}")
