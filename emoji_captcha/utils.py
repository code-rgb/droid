import asyncio
import traceback
from functools import partial, wraps
from typing import Any, Awaitable, Callable


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
