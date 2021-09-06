import asyncio
import traceback
from functools import partial, wraps
from typing import Any, Awaitable, Callable, Optional

from pyrogram.types.messages_and_media.message import Message


def format_exception(exc) -> str:
    return "".join(
        traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)
    )


def run_sync(func: Callable[..., Any]) -> Awaitable[Any]:
    """Runs the given sync function (optionally with arguments) on a separate thread."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    return wrapper


def get_media(msg: Message):
    available_media = (
        "audio",
        "document",
        "photo",
        "sticker",
        "animation",
        "video",
        "voice",
        "video_note",
        "new_chat_photo",
    )
    for kind in available_media:
        media = getattr(msg, kind, None)
        if media is not None:
            break
    else:
        media = None
    return media


def get_file_id(msg) -> Optional[str]:
    if media := get_media(msg):
        return media.file_id
