import asyncio
import traceback
from functools import partial, wraps
from typing import Any, Awaitable, Callable, Optional, Tuple, Union
import logging
from pyrogram.types.messages_and_media.message import Message

logger = logging.getLogger(__name__)


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


async def run_command(
    *args: Any, shell: bool = False
) -> Tuple[Union[asyncio.subprocess.Process, str, int, None]]:
    """Run Command in Shell

    Parameters:
    ----------
        - shell (`bool`, optional): For single commands. (Defaults to `False`)

    Returns:
    -------
        `Tuple[Union[asyncio.subprocess.Process, str, int, None]]`: (stdout, stderr, return_code, Process)
    """
    try:
        if shell:
            proc = await asyncio.create_subprocess_shell(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        std_out, std_err = await proc.communicate()
    except Exception:
        logger.exception(f"Failed to run command => {''.join(args)}")
        return_code = 1
        out, err = ("", "")
        proc = None
    else:
        return_code = proc.returncode
        out = std_out.decode("utf-8", "replace").strip()
        err = std_err.decode("utf-8", "replace").strip()
    return (out, err, return_code, proc)
