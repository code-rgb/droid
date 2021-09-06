from pyrogram import Client
import asyncio
from os import getenv
from pathlib import Path

ENV = Path("config.env")
if ENV.is_file():
    from dotenv import load_dotenv

    load_dotenv(ENV)


async def main(api_id: int, api_hash: str) -> None:
    async with Client(":memory:", api_id, api_hash) as app:
        session = await app.export_session_string()
        await app.send_message("me", f"Your `STRING_SESSION` is:\n```{session}```")


if __name__ == "__main__":
    api_id = getenv("API_ID") or input("Enter API_ID: ")
    api_hash = getenv("API_HASH") or input("Enter API_HASH: ")
    asyncio.run(main(int(api_id), api_hash))
