from contextlib import asynccontextmanager
from enum import Enum
from logging import getLogger
from typing import Any, AsyncIterator, Mapping, Optional, TypeVar, Union

from aiolimiter import AsyncLimiter
from httpx import Proxy, Request, URL

# noinspection PyProtectedMember
from httpx._client import ClientState, USE_CLIENT_DEFAULT, UseClientDefault

# noinspection PyProtectedMember
from httpx._types import (
    AuthTypes,
    CookieTypes,
    HeaderTypes,
    ProxiesTypes,
    QueryParamTypes as _QueryParamTypes,
    RequestContent,
    RequestData,
    RequestExtensions,
    RequestFiles,
    TimeoutTypes,
    URLTypes,
)

from async_pixiv.error import RateLimitError
from async_pixiv.utils.bypass import BypassAsyncHTTPTransport
from async_pixiv.utils.enums import Enum as PixivEnum
from async_pixiv.utils.overwrite import AsyncHTTPTransport, Response, AsyncClient

__all__ = ("Net",)

QueryParamTypes = TypeVar(
    "QueryParamTypes",
    bound=Union[_QueryParamTypes, Mapping[str, Union[Enum, PixivEnum, "SearchFilter"]]],
)

logger = getLogger(__name__)


def get_proxy_map(
    proxies: Optional[ProxiesTypes], allow_env_proxies: bool
) -> dict[str, Proxy | None]:
    if proxies is None:
        if allow_env_proxies:
            # noinspection PyProtectedMember
            from httpx._utils import get_environment_proxies

            return {
                key: None if url is None else Proxy(url=url)
                for key, url in get_environment_proxies().items()
            }
        return {}
    if isinstance(proxies, dict):
        new_proxies = {}
        for key, value in proxies.items():
            proxy = Proxy(url=value) if isinstance(value, (str, URL)) else value
            new_proxies[str(key)] = proxy
        return new_proxies
    else:
        proxy = Proxy(url=proxies) if isinstance(proxies, (str, URL)) else proxies
        return {"all://": proxy}


class NullLimiter(AsyncLimiter):
    def __init__(self, *_, **__):
        super().__init__(1)

    async def acquire(self, *_, **__) -> None:
        return


class Net(object):
    _headers: HeaderTypes = {}
    _client: AsyncClient | None = None
    _limiter: AsyncLimiter | None = None

    def __init__(
        self,
        *,
        max_rate: float | None = None,
        time_period: float = 60,
        trust_env: bool = True,
        proxies: Optional["ProxiesTypes"] = None,
        bypass: bool = False,
        timeout: TimeoutTypes = 10,
        retry: int = 5,
        retry_sleep: float = 1.0,
    ) -> None:
        if max_rate is not None and max_rate > 0:
            self._limiter = AsyncLimiter(max_rate, time_period)
        else:
            self._limiter = NullLimiter()

        proxy_map = get_proxy_map(proxies, trust_env)
        self._retry = retry
        self._retry_sleep = max(retry_sleep, 0)
        if bypass:
            self._client = AsyncClient(
                mounts={
                    k: BypassAsyncHTTPTransport(proxy=v) for k, v in proxy_map.items()
                },
                transport=BypassAsyncHTTPTransport(),
                timeout=timeout,
                proxies=proxies,
                trust_env=trust_env,
            )
        else:
            self._client = AsyncClient(
                mounts={k: AsyncHTTPTransport(proxy=v) for k, v in proxy_map.items()},
                transport=AsyncHTTPTransport(),
                timeout=timeout,
                proxies=proxies,
                trust_env=trust_env,
            )

    # noinspection PyAttributeOutsideInit,PyProtectedMember
    async def _send(self, request, *, stream, auth, follow_redirects) -> Response:
        if self._client._state == ClientState.CLOSED:
            raise RuntimeError("Cannot send a request, as the client has been closed.")

        self._client._state = ClientState.OPENED
        follow_redirects = (
            self._client.follow_redirects
            if isinstance(follow_redirects, UseClientDefault)
            else follow_redirects
        )

        auth = self._client._build_request_auth(request, auth)

        response = await self._client._send_handling_auth(
            request,
            auth=auth,
            follow_redirects=follow_redirects,
            history=[],
        )
        try:
            if not stream:
                await response.aread()

            return response.raise_for_result().raise_for_status()

        except BaseException as exc:  # pragma: no cover
            await response.aclose()
            raise exc

    async def send(
        self,
        request: "Request",
        *,
        stream: bool = False,
        auth: Union["AuthTypes", "UseClientDefault", None] = USE_CLIENT_DEFAULT,
        follow_redirects: Union[bool, "UseClientDefault"] = True,
    ) -> Response:
        import asyncio

        error: BaseException | None = None
        while (n := 0) < self._retry:
            async with self._limiter:
                try:
                    return await self._send(
                        request,
                        stream=stream,
                        auth=auth,
                        follow_redirects=follow_redirects,
                    )
                except RateLimitError:
                    logger.error(f"Rate limit. Retrying in {self._retry_sleep}s.")
                    n -= 1
                    await asyncio.sleep(self._retry_sleep)
                except Exception as exc:
                    error = exc
                    logger.warning(
                        f"Request Error: {exc}. "
                        f"Will retry in {self._retry_sleep}s. ({n + 1}th retry)"
                    )
                    await asyncio.sleep(self._retry_sleep)
        if error is not None:
            raise error

    async def request(
        self,
        method: str,
        url: "URLTypes",
        *,
        content: Optional["RequestContent"] = None,
        data: Optional["RequestData"] = None,
        files: Optional["RequestFiles"] = None,
        json: Optional[Any] = None,
        params: Optional["QueryParamTypes"] = None,
        headers: Optional["HeaderTypes"] = None,
        cookies: Optional["CookieTypes"] = None,
        auth: Union["AuthTypes", "UseClientDefault", None] = USE_CLIENT_DEFAULT,
        follow_redirects: Union[bool, "UseClientDefault"] = USE_CLIENT_DEFAULT,
        timeout: Union["TimeoutTypes", "UseClientDefault"] = USE_CLIENT_DEFAULT,
        extensions: Optional["RequestExtensions"] = None,
    ) -> Response:
        for k, v in (params := dict(params or {})).items():
            if isinstance(v, (Enum, PixivEnum)):
                params[k] = v.value
        request = self._client.build_request(
            method=method,
            url=str(url),
            content=content,
            data=data,
            files=files,
            json=json,
            params={k: v for k, v in (params or {}).items() if v is not None},
            headers={
                k: v
                for k, v in (dict(self._headers) | dict(headers or {})).items()
                if v is not None
            },
            cookies=cookies,
            timeout=timeout,
            extensions=extensions,
        )
        return await self.send(request, auth=auth, follow_redirects=follow_redirects)

    @asynccontextmanager
    async def stream(
        self,
        method: str,
        url: "URLTypes",
        *,
        content: Optional["RequestContent"] = None,
        data: Optional["RequestData"] = None,
        files: Optional["RequestFiles"] = None,
        json: Optional[Any] = None,
        params: Optional["QueryParamTypes"] = None,
        headers: Optional["HeaderTypes"] = None,
        cookies: Optional["CookieTypes"] = None,
        auth: Union["AuthTypes", "UseClientDefault", None] = USE_CLIENT_DEFAULT,
        follow_redirects: Union[bool, "UseClientDefault"] = USE_CLIENT_DEFAULT,
        timeout: Union["TimeoutTypes", "UseClientDefault"] = USE_CLIENT_DEFAULT,
        extensions: Optional["RequestExtensions"] = None,
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
        response = await self.send(
            request=request,
            auth=auth,
            follow_redirects=follow_redirects,
            stream=True,
        )
        try:
            yield response
        finally:
            await response.aclose()

    async def get(
        self,
        url: URLTypes,
        *,
        params: Optional["QueryParamTypes"] = None,
        headers: Optional["HeaderTypes"] = None,
        cookies: Optional["CookieTypes"] = None,
        auth: Union["AuthTypes", "UseClientDefault", None] = USE_CLIENT_DEFAULT,
        follow_redirects: Union[bool, "UseClientDefault"] = USE_CLIENT_DEFAULT,
        timeout: Union["TimeoutTypes", "UseClientDefault"] = USE_CLIENT_DEFAULT,
        extensions: Optional["RequestExtensions"] = None,
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

    async def options(
        self,
        url: URLTypes,
        *,
        params: Optional["QueryParamTypes"] = None,
        headers: Optional["HeaderTypes"] = None,
        cookies: Optional["CookieTypes"] = None,
        auth: Union["AuthTypes", "UseClientDefault", None] = USE_CLIENT_DEFAULT,
        follow_redirects: Union[bool, "UseClientDefault"] = USE_CLIENT_DEFAULT,
        timeout: Union["TimeoutTypes", "UseClientDefault"] = USE_CLIENT_DEFAULT,
        extensions: Optional["RequestExtensions"] = None,
    ) -> Response:
        return await self.request(
            "OPTIONS",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )

    async def head(
        self,
        url: URLTypes,
        *,
        params: Optional["QueryParamTypes"] = None,
        headers: Optional["HeaderTypes"] = None,
        cookies: Optional["CookieTypes"] = None,
        auth: Union["AuthTypes", "UseClientDefault", None] = USE_CLIENT_DEFAULT,
        follow_redirects: Union[bool, "UseClientDefault"] = USE_CLIENT_DEFAULT,
        timeout: Union["TimeoutTypes", "UseClientDefault"] = USE_CLIENT_DEFAULT,
        extensions: Optional["RequestExtensions"] = None,
    ) -> Response:
        return await self.request(
            "HEAD",
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
        content: Optional["RequestContent"] = None,
        data: Optional["RequestData"] = None,
        files: Optional["RequestFiles"] = None,
        json: Optional[Any] = None,
        params: Optional["QueryParamTypes"] = None,
        headers: Optional["HeaderTypes"] = None,
        cookies: Optional["CookieTypes"] = None,
        auth: Union["AuthTypes", "UseClientDefault", None] = USE_CLIENT_DEFAULT,
        follow_redirects: Union[bool, "UseClientDefault"] = USE_CLIENT_DEFAULT,
        timeout: Union["TimeoutTypes", "UseClientDefault"] = USE_CLIENT_DEFAULT,
        extensions: Optional["RequestExtensions"] = None,
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

    async def put(
        self,
        url: URLTypes,
        *,
        content: Optional["RequestContent"] = None,
        data: Optional["RequestData"] = None,
        files: Optional["RequestFiles"] = None,
        json: Optional[Any] = None,
        params: Optional["QueryParamTypes"] = None,
        headers: Optional["HeaderTypes"] = None,
        cookies: Optional["CookieTypes"] = None,
        auth: Union["AuthTypes", "UseClientDefault", None] = USE_CLIENT_DEFAULT,
        follow_redirects: Union[bool, "UseClientDefault"] = USE_CLIENT_DEFAULT,
        timeout: Union["TimeoutTypes", "UseClientDefault"] = USE_CLIENT_DEFAULT,
        extensions: Optional["RequestExtensions"] = None,
    ) -> Response:
        return await self.request(
            "PUT",
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

    async def patch(
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
        auth: Union[AuthTypes, UseClientDefault] = USE_CLIENT_DEFAULT,
        follow_redirects: Union[bool, UseClientDefault] = USE_CLIENT_DEFAULT,
        timeout: Union[TimeoutTypes, UseClientDefault] = USE_CLIENT_DEFAULT,
        extensions: Optional[RequestExtensions] = None,
    ) -> Response:
        return await self.request(
            "PATCH",
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

    async def delete(
        self,
        url: URLTypes,
        *,
        params: Optional["QueryParamTypes"] = None,
        headers: Optional["HeaderTypes"] = None,
        cookies: Optional["CookieTypes"] = None,
        auth: Union["AuthTypes", "UseClientDefault", None] = USE_CLIENT_DEFAULT,
        follow_redirects: Union[bool, "UseClientDefault"] = USE_CLIENT_DEFAULT,
        timeout: Union["TimeoutTypes", "UseClientDefault"] = USE_CLIENT_DEFAULT,
        extensions: Optional["RequestExtensions"] = None,
    ) -> Response:
        return await self.request(
            "DELETE",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )
