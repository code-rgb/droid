import asyncio
import logging
import sys

import aiorun
from pyrogram.session import Session

from . import log
from .core import Bot

logger = logging.getLogger("Main")
log.setup_log()
aiorun.logger.disabled = True
Session.notice_displayed = True


def main():
    logger.info("Starting...")
    if sys.platform == "win32":
        policy = asyncio.WindowsProactorEventLoopPolicy()
    else:
        try:
            import uvloop
        except ImportError:
            logger.info("Uvloop is not installed, skipping...")
            policy = asyncio.DefaultEventLoopPolicy()
        else:
            logger.info("Uvloop found.")
            policy = uvloop.EventLoopPolicy()

    logger.info(f"Using {policy.__class__.__name__}.")
    asyncio.set_event_loop_policy(policy)
    loop = asyncio.new_event_loop()
    aiorun.run(Bot.begin(loop=loop), loop=loop)
