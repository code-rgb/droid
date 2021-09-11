from typing import Dict
from iytdl import Process, iYTDL
from iytdl.constants import YT_VID_URL
from iytdl.exceptions import NoResultFoundError, DownloadFailedError
from pyrogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultPhoto,
    InputMediaPhoto,
)
from .. import mod
from ..decor import OnCallback, OnInline
from ..config import CONFIG


class YoutubeDL(mod.Module):
    YT_REGEX: Dict[str, str] = {
        "inline": r"yt (.+)",
        "next": r"^yt_(back|next)\|(?P<key>[\w-]{5,11})\|(?P<pg>\d+)-(?P<user_id>\d+)$",
        "list_all": r"^yt_listall\|(?P<key>[\w-]{5,11})-(?P<user_id>\d+)$",
        "extract_info": r"^yt_extract_info\|(?P<key>[\w-]{5,11})-(?P<user_id>\d+)$",
        "download": r"yt_(?P<mode>gen|dl)\|(?P<key>[\w-]+)\|(?P<choice>[\w-]+)\|(?P<dl_type>a|v)-(?P<user_id>\d+)$",
        "cancel": r"^yt_cancel\|(?P<process_id>[\w\.]+)-(?P<user_id>\d+)$",
    }

    async def on_load(self) -> None:
        self.ytdl = await iYTDL.init(
            session=self.bot.http,
            silent=True,
            loop=self.bot.loop,
            log_group_id=CONFIG.log_channel_id,
            cache_path="cache",
            delete_media=True,
        )

    async def on_exit(self) -> None:
        await self.ytdl.stop()

    @OnInline(YT_REGEX["inline"])
    async def on_inline(self, i_q: InlineQuery):
        query = i_q.matches[0].group(1)
        try:
            data = await self.ytdl.parse(query, extract=False)
        except NoResultFoundError:
            return
        await i_q.answer(
            results=[
                InlineQueryResultPhoto(
                    photo_url=data.image_url,
                    title=f"🔍 {query}",
                    description="powered by iYTDL",
                    caption=data.caption,
                    reply_markup=data.buttons.add(i_q.from_user.id),
                ),
            ],
            cache_time=1,
        )

    @OnCallback(YT_REGEX["next"])
    async def callback_next(self, c_q: CallbackQuery):
        match = c_q.matches[0]
        if c_q.from_user.id not in (int(match.group("user_id")), *CONFIG.owner_id):
            await c_q.answer("This message is not for you !", show_alert=True)
            return

        if match.group(1) == "next":
            index = int(match.group("pg")) + 1
        else:
            index = int(match.group("pg")) - 1
        if data := await self.ytdl.next_result(key=match.group("key"), index=index):
            await c_q.edit_message_media(
                media=(
                    InputMediaPhoto(
                        media=data.image_url,
                        caption=data.caption,
                    )
                ),
                reply_markup=data.buttons.add(c_q.from_user.id),
            )
        else:
            await c_q.answer("That's All Folks !", show_alert=True)

    @OnCallback(YT_REGEX["list_all"])
    async def callback_listall(self, c_q: CallbackQuery):
        match = c_q.matches[0]
        if c_q.from_user.id not in (int(match.group("user_id")), *CONFIG.owner_id):
            await c_q.answer("This message is not for you !", show_alert=True)
            return
        await c_q.answer()
        media, buttons = await self.ytdl.listview(match.group("key"))
        await c_q.edit_message_media(media=media, reply_markup=buttons)

    @OnCallback(YT_REGEX["extract_info"])
    async def extract_info(self, c_q: CallbackQuery):
        match = c_q.matches[0]
        if c_q.from_user.id not in (int(match.group("user_id")), *CONFIG.owner_id):
            await c_q.answer("This message is not for you !", show_alert=True)
            return
        await c_q.answer("Please Wait...")
        key = match.group("key")
        if data := await self.ytdl.extract_info_from_key(key):
            if len(key) == 11:
                await c_q.edit_message_text(
                    text=data.caption,
                    reply_markup=data.buttons.add(c_q.from_user.id),
                )
            else:
                await c_q.edit_message_media(
                    media=(
                        InputMediaPhoto(
                            media=data.image_url,
                            caption=data.caption,
                        )
                    ),
                    reply_markup=data.buttons.add(c_q.from_user.id),
                )

    @OnCallback(YT_REGEX["download"])
    async def yt_download(self, c_q: CallbackQuery):
        match = c_q.matches[0]
        user_id = int(match.group("user_id"))
        if c_q.from_user.id not in (user_id, *CONFIG.owner_id):
            await c_q.answer("This message is not for you !", show_alert=True)
            return

        if match.group("mode") == "gen":
            yt_url = False
            video_link = await self.ytdl.cache.get_url(match.group("key"))
        else:
            yt_url = True
            video_link = f"{YT_VID_URL}{match.group('key')}"
        self.log.info(f"URL: [{video_link}]")

        media_type = "video" if match.group("dl_type") == "v" else "audio"

        uid, disp_str = self.ytdl.get_choice_by_id(
            match.group("choice"), media_type, yt_url=yt_url
        )

        await c_q.answer(f"⬇️ Downloading - {disp_str}", show_alert=True)
        try:
            key = await self.ytdl.download(
                url=video_link,
                uid=uid,
                downtype=media_type,
                update=c_q,
                cb_extra=user_id,
            )
        except DownloadFailedError as e:
            self.log.error(f"Download Failed - {e}")
        else:
            await self.ytdl.upload(
                client=self.bot.client,
                key=key,
                downtype=media_type,
                update=c_q,
                caption_link=video_link,
                cb_extra=user_id,
            )

    @OnCallback(YT_REGEX["cancel"])
    async def yt_cancel(self, c_q: CallbackQuery):
        match = c_q.matches[0]
        if c_q.from_user.id not in (int(match.group("user_id")), *CONFIG.owner_id):
            await c_q.answer("This message is not for you !", show_alert=True)
            return

        await c_q.answer("Trying to Cancel Process..")
        process_id = match.group("process_id")
        Process.cancel_id(process_id)
        if c_q.message:
            await c_q.message.delete()
        else:
            await c_q.edit_message_text("✔️ `Stopped Successfully`")
