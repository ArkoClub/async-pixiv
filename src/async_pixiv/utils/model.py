import asyncio
import sys
from asyncio import Lock
from enum import Enum
from typing import (
    Any,
    List,
    Mapping,
    NamedTuple,
    Optional,
    TYPE_CHECKING,
)

from aiohttp import (
    ClientSession,
    ClientTimeout,
    TCPConnector,
)
from aiohttp.typedefs import (
    LooseHeaders,
    StrOrURL,
)
from aiohttp_socks import ProxyConnector
from typing_extensions import Self
from yarl import URL

from async_pixiv.utils.func import proxies_from_env
from async_pixiv.utils.typed import RequestMethod

try:
    import regex as re
except ImportError:
    import re

try:
    import ujson as json
except ImportError:
    import json

try:
    from uvloop import EventLoopPolicy
except ImportError:
    if sys.platform.startswith('win'):
        from asyncio import WindowsProactorEventLoopPolicy as EventLoopPolicy
    else:
        from asyncio import DefaultEventLoopPolicy as EventLoopPolicy

if TYPE_CHECKING:
    from aiohttp import ClientResponse

__all__ = ['Net']

asyncio.set_event_loop_policy(EventLoopPolicy())


class Config(NamedTuple):
    client_id: str
    client_secret: str
    user_agent: str


class Net(object):
    __slots__ = (
        '_conn_kwargs', '_timeout', '_session', '_proxies',
        '_trust_env',
    )

    _limit: int
    _timeout: ClientTimeout
    _trust_env: bool
    _proxies: Optional[List[URL]]
    _session: Optional[ClientSession]

    _aio_lock: Lock = Lock()

    async def _init_session(self) -> ClientSession:
        async with self._aio_lock:
            if self._session is None or self._session.closed:
                proxy: Optional[URL] = None

                for p in self._proxies:
                    if p.scheme in ['socks5', 'socks4', 'http', 'ws']:
                        proxy = p
                        break

                if (
                        proxy is not None
                        and
                        proxy.scheme in ['socks5', 'socks4', 'http']
                ):
                    connector = ProxyConnector.from_url(str(proxy))
                else:
                    connector = TCPConnector(**self._conn_kwargs)
                self._session = ClientSession(
                    connector=connector,
                    timeout=self._timeout,
                    json_serialize=json.dumps,
                )

        return self._session

    def __init__(
            self, *, limit: int = 30, timeout: float = 10,
            proxy: Optional[StrOrURL] = None, trust_env: bool = False
    ) -> None:
        self._session = None
        self._conn_kwargs = {'limit': limit}
        self._timeout = ClientTimeout(timeout)

        self._proxies = [URL(str(proxy))] if proxy is not None else []
        if trust_env:
            self._proxies.extend(proxies_from_env())
        self._proxies = list(set(self._proxies))

    async def __aenter__(self) -> Self:
        await self._init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._session.close()

    def __del__(self) -> None:
        if self._session and not self._session.closed:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()

            loop.run_until_complete(self._session.close())

    async def start(self) -> Self:
        await self._init_session()
        return self

    async def close(self) -> None:
        async with self._aio_lock:
            if self._session and not self._session.closed:
                await self._session.close()

    async def _request(
            self,
            method: RequestMethod,
            url: StrOrURL, *,
            params: Optional[Mapping[str, Any]] = None,
            headers: Optional[LooseHeaders] = None,
            data: Any = None,
    ) -> "ClientResponse":
        proxy = None
        for p in self._proxies:
            if p.scheme in ['http', 'ws']:
                proxy = p
                break
        param = dict()
        for key, value in (params or {}).items():
            if value in [None, {}, []]:
                continue
            if isinstance(value, Enum):
                value = value.value
            if isinstance(value, (str, int, float)):
                param.update({key: value})
            if isinstance(value, list):
                if key in ["sizes", "types"]:
                    param.update({key: ','.join(map(str, value))})
                elif key in ["ids"]:
                    param.update({
                        f"{key}[]": ",".join([str(pid) for pid in value])
                    })
                elif key in ["viewed"]:
                    [
                        param.update({f"{key}[{k}]": value[k]})
                        for k in range(len(value))
                    ]
                else:
                    param.update({f"{key}[]": ','.join(map(str, value))})
            if isinstance(value, bool):
                param.update({key: str(value).lower()})
        return await (await self._init_session()).request(
            method, url, params=param, headers=headers, data=data,
            proxy=proxy
        )

    async def get(
            self, url: StrOrURL, *, params: Optional[Mapping[str, Any]] = None,
            headers: Optional[LooseHeaders] = None, data: Any = None,
    ) -> "ClientResponse":
        return await self._request(
            'GET', url, params=params, headers=headers, data=data
        )

    async def post(
            self, url: StrOrURL, *, params: Optional[Mapping[str, Any]] = None,
            headers: Optional[LooseHeaders] = None, data: Any = None,
    ) -> "ClientResponse":
        return await self._request(
            'POST', url, params=params, headers=headers, data=data
        )

    async def head(
            self, url: StrOrURL, *, params: Optional[Mapping[str, Any]] = None,
            headers: Optional[LooseHeaders] = None, data: Any = None,
    ) -> "ClientResponse":
        return await self._request(
            'HEAD', url, params=params, headers=headers, data=data
        )

    async def put(
            self, url: StrOrURL, *, params: Optional[Mapping[str, Any]] = None,
            headers: Optional[LooseHeaders] = None, data: Any = None,
    ) -> "ClientResponse":
        return await self._request(
            "PUT", url, params=params, headers=headers, data=data
        )

    async def patch(
            self, url: StrOrURL, *, params: Optional[Mapping[str, Any]] = None,
            headers: Optional[LooseHeaders] = None, data: Any = None,
    ) -> "ClientResponse":
        return await self._request(
            "PATCH", url, params=params, headers=headers, data=data
        )

    async def delete(
            self, url: StrOrURL, *, params: Optional[Mapping[str, Any]] = None,
            headers: Optional[LooseHeaders] = None, data: Any = None,
    ) -> "ClientResponse":
        return await self._request(
            "DELETE", url, params=params, headers=headers, data=data
        )
