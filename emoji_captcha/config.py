import os
from pathlib import Path
from typing import Any, Dict

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from pyrogram.scaffold import Scaffold


class Config:
    def __init__(self) -> None:
        if os.path.isfile("config.env"):
            load_dotenv("config.env")

        config = dict(
            api_id=int(os.environ.get("API_ID", 0)),
            api_hash=os.environ.get("API_HASH"),
            bot_token=os.environ.get("BOT_TOKEN"),
            heroku_api_key=os.environ.get("HEROKU_API_KEY"),
            heroku_app_name=os.environ.get("HEROKU_APP"),
            workers=(lambda x: int(x) if x else Scaffold.WORKERS)(
                os.environ.get("WORKERS")
            ),
            cipher_key=(lambda x: x.encode("utf-8") if x else Fernet.generate_key())(
                os.environ.get("CIPHER_KEY")
            ),
            owner_id=int(os.environ.get("OWNER_ID", 0)),
            sleep_threshold=int(os.environ.get("SLEEP_THRESHOLD", 180)),
            down_path=Path(os.environ.get("DOWN_PATH", "Downloads")),
        )

        for key, value in config.items():
            setattr(self, key, value or None)

        # create Download Dir
        self.down_path.mkdir(exist_ok=True)

    @property
    def _client(self) -> Dict[str, Any]:
        return dict(
            map(
                lambda x: (x, getattr(self, x, None)),
                ("api_id", "api_hash", "bot_token", "workers", "sleep_threshold"),
            )
        )


config = Config()
