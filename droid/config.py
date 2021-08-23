import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from pyrogram.scaffold import Scaffold

if os.path.isfile("config.env"):
    load_dotenv("config.env")


def get_env(key: str, default: Any = None) -> Any:
    if value := os.getenv(key):
        value = value.strip()
    return value or default


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
    workdir: str = get_env("WORKDIR", "session")
    log_channel_id: int = int(get_env("LOG_CHANNEL_ID", 0))

    def __post_init__(self):
        self.down_path.mkdir(exist_ok=True)
        for attr in ("owner_id", "sudo_users"):
            value = list(
                filter(
                    None,
                    map(
                        lambda x: int(x) if x.isdigit() else None,
                        get_env(attr.upper(), "").split(),
                    ),
                )
            )
            setattr(
                self,
                attr,
                value,
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
                    "workers",
                    "sleep_threshold",
                    "workdir",
                ),
            )
        )


CONFIG = Config()
