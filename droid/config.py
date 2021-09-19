import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from pyrogram.scaffold import Scaffold

LOG = logging.getLogger(__name__)


def get_env(key: str, default: Any = None) -> Any:
    if value := os.getenv(key):
        value = value.strip()
    return value or default


if os.path.isfile("config.env"):
    load_dotenv("config.env")


if get_env("_____REMOVE_____THIS_____LINE_____"):
    LOG.error(
        (
            "Please remove the line mentioned in the first"
            " hashtag from the config.env file. Exiting!"
        )
    )
    sys.exit(1)


@dataclass
class Config:
    api_id: int = int(get_env("API_ID", 0))
    api_hash: str = get_env("API_HASH")
    bot_token: str = get_env("BOT_TOKEN")
    heroku_api_key: str = get_env("HEROKU_API_KEY")
    heroku_app_name: str = get_env("HEROKU_APP")
    workers: int = (lambda x: int(x) if x else Scaffold.WORKERS)(get_env("WORKERS"))
    owner_id: List[int] = field(default_factory=list)
    sudo_users: List[int] = field(default_factory=list)
    sleep_threshold: int = int(get_env("SLEEP_THRESHOLD", 180))
    down_path: Path = Path(get_env("DOWN_PATH", "downloads"))
    workdir: str = get_env("WORKDIR", "sessions")
    log_channel_id: int = int(get_env("LOG_CHANNEL_ID", 0))
    string_session: str = get_env("STRING_SESSION")
    max_caption_length: int = 1024
    max_text_length: int = 4096
    cmd_prefix: str = get_env("CMD_PREFIX", "/")

    def __post_init__(self):
        self.down_path.mkdir(exist_ok=True, parents=True)
        Path(self.workdir).mkdir(exist_ok=True, parents=True)
        for attr in ("owner_id", "sudo_users"):
            getattr(self, attr).extend(
                filter(
                    None,
                    map(
                        lambda x: int(x) if x.isdigit() else None,
                        get_env(attr.upper(), "").split(),
                    ),
                )
            )

    @property
    def _client(self) -> Dict[str, Any]:
        return dict(
            map(
                lambda x: (x, getattr(self, x, None)),
                (
                    "api_id",
                    "api_hash",
                    "bot_token",
                    "string_session",
                    "workers",
                    "sleep_threshold",
                    "workdir",
                ),
            )
        )


CONFIG = Config()
