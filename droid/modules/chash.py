import asyncio
import hashlib
from typing import List, Union
from ..core.command_context import Ctx
from PIL import Image
from pyrogram.types import User, Message
import os
import yaml
import imagehash
from .. import mod
from ..decor import OnCmd
from ..config import CONFIG
from collections import defaultdict

CHNL_ID = -1001561287539
SPRC_ID = -1001426404283
IMG_HASH_TYPES = (
    "phash",
    "average_hash",
    "whash",
    "dhash_vertical",
    "dhash",
    "phash_simple",
)


def md5_hash(data: Union[str, bytes]) -> str:
    if isinstance(data, str):
        data = data.encode(encoding="UTF-8")
    return hashlib.md5(data).hexdigest()


class Chash(mod.Module):
    @OnCmd("chash")
    async def on_message(self, ctx: Ctx):
        reply = ctx.msg.reply_to_message
        if not (reply.text or reply.photo):
            await ctx.err("Reply to a 'Message' or 'Photo' first!", del_in=5)
            return
        msg = await ctx.edit("`Processing...`")
        info_dict = defaultdict(dict)
        if reply.photo:
            scam_img = await reply.download()
            with Image.open(scam_img) as img:
                info_dict["MD5"]["image"] = md5_hash(img.tobytes())
                if reply.caption:
                    info_dict["MD5"]["text"] = md5_hash(reply.caption)
                for img_hash in IMG_HASH_TYPES:
                    info_dict["HASH"][img_hash] = str(getattr(imagehash, img_hash)(img))
            if os.path.isfile(scam_img):
                os.remove(scam_img)
        else:
            info_dict["MD5"]["text"] = md5_hash(reply.text)

        for i in ("id", "title", "username"):
            if k := getattr(reply.chat, i):
                info_dict["CHAT"][i] = k
        info_dict["CHAT"]["msg_id"] = reply.message_id
        if scmr := reply.forward_sender_name:
            info_dict["USER"]["name"] = scmr
        elif scmr := (reply.forward_from or reply.from_user):
            info_dict["USER"]["id"] = scmr.id
            info_dict["USER"]["name"] = " ".join(
                (scmr.first_name or "", scmr.last_name or "")
            )
            if scmr.username:
                info_dict["USER"]["username"] = scmr.username
        info_str = f"<pre>{yaml.dump(dict(info_dict), sort_keys=False, default_flow_style=False, encoding='utf-8')}</pre>"
        if reply.photo:
            if len(info_str) > CONFIG.max_caption_length:
                image_ = await reply.copy(CHNL_ID, caption="")
                stored = await image_.reply_text(info_str, parse_mode="html")
            else:
                stored = await reply.copy(CHNL_ID, caption=info_str, parse_mode="html")
        else:
            stored = await self.bot.send_message(CHNL_ID, info_str, parse_mode="html")
        m_flags = ["-r", "-f", "-d"] if "-x" in ctx.flags else list(ctx.flags)
        await asyncio.gather(
            msg.edit_text(
                f"☑️ <b>Hashed Successfully</b> (#ID <a href={stored.link}>{stored.message_id}</a> )",
                parse_mode="HTML",
                disable_web_page_preview=True,
            ),
            parse_flags(m_flags, reply, scmr),
        )


async def parse_flags(flags: List[str], msg: Message, user: User) -> None:
    tasks: List = []
    if "-r" in flags:
        tasks.append(msg.forward(SPRC_ID))
    if user and hasattr(user, "id"):
        if "-f" in flags:
            tasks.append(msg.reply(f"/fban {user.id}", del_in=10))
        if "-b" in flags:
            tasks.append(msg.chat.kick_member(user.id))
    if "-d" in flags:
        tasks.append(msg.delete())
    await asyncio.gather(*tasks)
