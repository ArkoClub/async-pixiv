import asyncio
from contextlib import asynccontextmanager
from logging import getLogger
from typing import Any, AsyncIterator, Dict, Optional, Union

from aiolimiter import AsyncLimiter

# noinspection PyProtectedMember
from httpx import AsyncClient, URL

# noinspection PyProtectedMember
from httpx._client import USE_CLIENT_DEFAULT, UseClientDefault

# noinspection PyProtectedMember
from httpx._config import Proxy

# noinspection PyProtectedMember
from httpx._types import (
    AuthTypes,
    CookieTypes,
    HeaderTypes,
    ProxiesTypes,
    QueryParamTypes,
    RequestContent,
    RequestData,
    RequestExtensions,
    RequestFiles,
    TimeoutTypes,
    URLTypes,
)

# noinspection PyProtectedMember
from httpx._utils import get_environment_proxies
from yarl import URL

from async_pixiv.utils.context import async_do_nothing
from async_pixiv.utils.bypass import BypassAsyncHTTPTransport
from async_pixiv.utils.overwrite import AsyncHTTPTransport, Response

try:
    import regex as re
except ImportError:
    import re

try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    uvloop = None

__all__ = ["Net"]

logger = getLogger(__name__)


class Net:
    _client: AsyncClient

    @property
    def client(self) -> AsyncClient:
        return self._client

    # noinspection PyProtectedMember
    def __init__(
        self,
        *,
        rate_limiter: Optional[AsyncLimiter] = AsyncLimiter(100),
        proxies: Optional[ProxiesTypes] = None,
        retry: Optional[int] = 5,
        retry_sleep: float = 1,
        bypass: bool = False,
        transport_kwargs: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        transport_kwargs = transport_kwargs or {}
        self._rate_limiter = rate_limiter
        if proxies is None:
            proxy_map = {
                key: None if url is None else Proxy(url=url)
                for key, url in get_environment_proxies().items()
            }
        elif isinstance(proxies, dict):
            new_proxies = {}
            for key, value in proxies.items():
                proxy = Proxy(url=value) if isinstance(value, (str, URL)) else value
                new_proxies[str(key)] = proxy
            proxy_map = new_proxies
        else:
            proxy = Proxy(url=proxies) if isinstance(proxies, (str, URL)) else proxies
            proxy_map = {"all://": proxy}

        for i in filter(lambda x: x in kwargs, ["mounts", "transport", "proxies"]):
            del kwargs[i]
        self._retry = retry
        self._retry_sleep = max(retry_sleep, 0)
        if bypass:
            self._client = AsyncClient(
                mounts={
                    k: BypassAsyncHTTPTransport(proxy=v) for k, v in proxy_map.items()
                },
                transport=BypassAsyncHTTPTransport(),
                **kwargs,
            )
        else:
            self._client = AsyncClient(
                mounts={
                    k: AsyncHTTPTransport(proxy=v, **transport_kwargs)
                    for k, v in proxy_map.items()
                },
                transport=AsyncHTTPTransport(**transport_kwargs),
                **kwargs,
            )

    async def request(
        self,
        method: str,
        url: URLTypes,
        *,
        content: Optional[RequestContent] = None,
        data: Optional[RequestData] = None,
        files: Optional[RequestFiles] = None,
        json: Optional[Any] = None,
        params: Optional[QueryParamTypes] = None,
        headers: Optional[HeaderTypes] = None,
        cookies: Optional[CookieTypes] = None,
        auth: Union[AuthTypes, UseClientDefault, None] = USE_CLIENT_DEFAULT,
        follow_redirects: Union[UseClientDefault, bool] = USE_CLIENT_DEFAULT,
        timeout: Union[UseClientDefault, TimeoutTypes] = USE_CLIENT_DEFAULT,
        extensions: Optional[RequestExtensions] = None,
    ) -> Response:
        request = self._client.build_request(
            method=method,
            url=url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            extensions=extensions,
        )
        error = None
        times = max(1, self._retry)
        for n in range(times):
            try:
                # noinspection PyArgumentList
                async with (self._rate_limiter or async_do_nothing()):
                    return await self._client.send(
                        request, auth=auth, follow_redirects=follow_redirects
                    )
            except Exception as e:
                error = e
                logger.warning(
                    f"Request Error: {e}. "
                    f"Will retry in {self._retry_sleep}s. ({n + 1}th retry)"
                )
                await asyncio.sleep(self._retry_sleep)
        if error is not None:
            raise error

    async def get(
        self,
        url: URLTypes,
        *,
        params: Optional[QueryParamTypes] = None,
        headers: Optional[HeaderTypes] = None,
        cookies: Optional[CookieTypes] = None,
        auth: Union[AuthTypes, UseClientDefault, None] = USE_CLIENT_DEFAULT,
        follow_redirects: Union[UseClientDefault, bool] = USE_CLIENT_DEFAULT,
        timeout: Union[UseClientDefault, TimeoutTypes] = USE_CLIENT_DEFAULT,
        extensions: Optional[RequestExtensions] = None,
    ) -> Response:
        return await self.request(
            "GET",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )

    async def post(
        self,
        url: URLTypes,
        *,
        content: Optional[RequestContent] = None,
        data: Optional[RequestData] = None,
        files: Optional[RequestFiles] = None,
        json: Optional[Any] = None,
        params: Optional[QueryParamTypes] = None,
        headers: Optional[HeaderTypes] = None,
        cookies: Optional[CookieTypes] = None,
        auth: Union[AuthTypes, UseClientDefault, None] = USE_CLIENT_DEFAULT,
        follow_redirects: Union[UseClientDefault, bool] = USE_CLIENT_DEFAULT,
        timeout: Union[UseClientDefault, TimeoutTypes] = USE_CLIENT_DEFAULT,
        extensions: Optional[RequestExtensions] = None,
    ) -> Response:
        return await self.request(
            "POST",
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )

    @asynccontextmanager
    async def stream(
        self,
        method: str,
        url: URLTypes,
        *,
        content: Optional[RequestContent] = None,
        data: Optional[RequestData] = None,
        files: Optional[RequestFiles] = None,
        json: Optional[Any] = None,
        params: Optional[QueryParamTypes] = None,
        headers: Optional[HeaderTypes] = None,
        cookies: Optional[CookieTypes] = None,
        auth: Union[AuthTypes, UseClientDefault, None] = USE_CLIENT_DEFAULT,
        follow_redirects: Union[UseClientDefault, bool] = USE_CLIENT_DEFAULT,
        timeout: Union[UseClientDefault, TimeoutTypes] = USE_CLIENT_DEFAULT,
        extensions: Optional[RequestExtensions] = None,
    ) -> AsyncIterator[Response]:
        request = self._client.build_request(
            method=method,
            url=url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            extensions=extensions,
        )
        response = await self._client.send(
            request=request,
            auth=auth,
            follow_redirects=follow_redirects,
            stream=True,
        )
        try:
            yield response
        finally:
            await response.aclose()

    async def close(self) -> None:
        return await self._client.aclose()
