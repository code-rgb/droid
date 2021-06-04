import asyncio
import logging
import os
import random
from io import BytesIO
from shutil import rmtree
from time import perf_counter
from typing import Dict, List, Set, Union
from urllib.parse import urlparse
import ujson
from bs4 import BeautifulSoup as soup
from cryptography.fernet import Fernet
from PIL import Image
from pyrogram import emoji
from pyrogram.types import InlineKeyboardButton
from pathlib import Path
import aiofiles


# Errors
class EmojiLoadFailed(Exception):
    pass


class Cipher(Fernet):
    def __init__(self, cipher_key: bytes):
        super().__init__(key=cipher_key)

    def __process_data(self, data: Union[str, bytes], mode: str) -> str:
        if not isinstance(data, bytes):
            data = data.encode()
        return (
            super().encrypt(data) if mode == "encrypt" else super().decrypt(data)
        ).decode("utf-8")

    def encrypt(self, data: Union[str, bytes]) -> str:
        return self.__process_data(data=data, mode="encrypt")

    def decrypt(self, data: Union[str, bytes]) -> str:
        return self.__process_data(data=data, mode="decrypt")

    def decode_markup(self, markup: List[List[InlineKeyboardButton]]) -> str:
        data = ""
        for row in markup:
            for btn in row:
                data += btn.callback_data.split(":")[-1]
        return self.decrypt(data.strip())


class EmojiCaptcha(ABC):
    cipher: Cipher
    total_emoji = int
    _emoji_source: Dict[str, str]
    _emoji_data: Path
    _is_loaded: bool

    def __init__(self):
        self.cipher = Cipher(self.config.cipher_key)
        self._emoji_source = {
            "url": "https://emojipedia.org",
            "name": "apple",
            "version": "ios-12.2",
        }
        self._emoji_data = Path(f"{self.__class__.__name__.lower()}.txt")
        self._is_loaded = self._emoji_data.is_file() and any(
            self.config.down_path.iterdir()
        )
        super().__init__()

    async def emoji_load(self) -> None:
        start = perf_counter()
        self.log.info("Loading emojis...")
        if self._is_loaded:
            with self._emoji_data.open("r") as ed:
                self.total_emoji = len(ujson.load(ed))
        else:
            await self.get_source_emoji()
        self.log.info(f"Done !  ⌛️ Loaded in {round(perf_counter() - start, 4)} sec")
        self.log.info(f"No. of loaded EMOJI: {self.total_emoji}")

    def get_pyro_emoji(self) -> Set[str]:
        self.log.info("Loading emoji from pyrogram.")
        return set(
            [
                e.lower().replace("_", "-")
                for e in dir(emoji)
                if (
                    not e.startswith("_")
                    and (e_value := getattr(emoji, e, None))
                    and len(e_value) == 1
                )
            ]
        )

    async def get_baseimg(self) -> Optional[str]:
        base_img_url = "https://github.com/code-rgb/pyrocaptcha/raw/main/base_img.png"
        base_img = Path(base_img_url.rsplit("/", 1)[1])
        if not base_img.is_file():
            async with self.http.get(base_img_url) as resp:
                if not resp.status != 200:
                    return
                img_bytes = await resp.read()
            with base_img.open("wb") as f:
                f.write(img_bytes)
        return str(base_img)

    async def get_source_emoji(self) -> None:
        url = "/".join(self._emoji_source.values())
        self.log.info(f"Fetching emojis from '{url}'.")
        async with self.http.get(url) as resp:
            if resp.status != 200:
                raise EmojiLoadFailed(f"Status: {resp.status}, Unable to GET '{url}'")
            text = await resp.text()
        pyro_emoji = self.get_pyro_emoji()
        self.log.info(f"Downloading emoji...")
        await self.download_emoji_imgs(
            dict(
                filter(
                    lambda x: x[1] and (x[0] in pyro_emoji),
                    map(
                        lambda x: (
                            x.a.get("href")[:-1].split("/")[-1],
                            (x.a.img.get("data-src") or "").replace(
                                "thumbs/72", "thumbs/320"
                            ),
                        ),
                        soup(text, "lxml")
                        .find("ul", {"class": "emoji-grid"})
                        .findAll("li"),
                    ),
                )
            )
        )

    async def save_to_file(
        self, url: str, filename: str, ext: str = "png"
    ) -> Optional[str]:
        async with self.http.get(url) as resp:
            if resp.status != 200:
                return
            img_bytes = await resp.read()
        try:
            async with aiofiles.open(f"{filename}.{ext}", mode="wb") as f:
                await f.write(img_bytes)
        except Exception as e:
            self.log.error(f"{e.__class__.__name__}: {e}")
        else:
            return filename

    async def download_emoji_imgs(self, emojis: Dict[str, str]) -> None:
        rmtree(self.config.down_path, ignore_errors=True)
        self.down_path.mkdir(exist_ok=True)
        tasks = [
            asyncio.ensure_future(save_to_file(url=img_url, filename=emoji_name))
            for emoji_name, img_url in emojis.items()
        ]
        self.log.info(f"  Preparing to Download {len(tasks)} files ...")
        all_emojis = await asyncio.gather(*tasks)
        self.log.info("  Done, Downloaded Sucessfully !")
        emoji_keys = list(filter(None, all_emojis))
        self.total_emoji = len(emoji_keys)
        with self._emoji_data.open("w") as fb:
            ujson.dump(emoji_keys, fb)

    def get_random(self, number: int = 15) -> Union[List[str], str]:
        with self._emoji_data.open("r") as f:
            random_e = random.sample(ujson.load(f), number)
        return random_e

    async def generate_captch_img(self, emo_list: List[str]) -> str:
        position = [(50, 87), (450, 25), (860, 50), (860, 545), (450, 545), (50, 545)]
        base_img = await self.get_baseimg()
        background = Image.open(base_img)
        for input_e, pos in zip(emo_list, position):
            image_paste = (
                Image.open(f"{self.config.down_path}/{input_e}.png")
                .convert("RGBA")
                .resize((380, 380), Image.LANCZOS)
                .rotate(random.randint(0, 360), expand=True)
            )
            background.paste(image_paste, pos, image_paste)
        img_io = BytesIO()
        background.save(img_io, format="PNG")
        img_io.name = "emoji_captcha.png"
        return img_io

    @staticmethod
    def choose_random(emo_lis: List[str]) -> List[str]:
        return random.sample(emo_list, 6)
