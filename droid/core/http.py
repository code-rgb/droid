import logging
from typing import Any, Dict, Optional, Union

import ujson
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ContentTypeError

LOG = logging.getLogger(__name__)


class Http:
    def __init__(self) -> None:
        self.session: Optional[ClientSession] = None
        super().__init__()

    @property
    def has_session(self) -> bool:
        return self.session and not self.session.closed

    @property
    def http(self) -> ClientSession:
        if not self.has_session:
            self.session = self.new_session()
        return self.session

    @staticmethod
    def new_session() -> ClientSession:
        return ClientSession(json_serialize=ujson.dumps)

    async def close_session(self) -> None:
        if self.has_session:
            await self.session.close()

    async def get_json(
        self,
        url: str,
        timeout: Union[ClientTimeout, float] = 10.0,
        ignore_errors: bool = False,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        if isinstance(timeout, (float, int)):
            timeout = ClientTimeout(total=timeout)
        kwargs["timeout"] = timeout
        try:
            async with self.http.get(url, **kwargs) as resp:
                if resp.status != 200:
                    raise ValueError(f"HTTP Status: {resp.status} - URL [{url}]")
                try:
                    return await resp.json(loads=ujson.loads)
                except ContentTypeError:
                    return ujson.loads(await resp.text())
        except Exception as e:
            if not ignore_errors:
                raise e
            LOG.exception(f"{e}: {e.__class__.__name__}")
