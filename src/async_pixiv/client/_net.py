from functools import lru_cache
from logging import getLogger

from httpx import (
    AsyncBaseTransport,
    QueryParams,
    Request,
    AsyncClient as DefaultAsyncClient,
)

# noinspection PyProtectedMember
from httpx._client import USE_CLIENT_DEFAULT, ClientState, UseClientDefault

# noinspection PyProtectedMember
from httpx._types import (
    HeaderTypes,
    ProxyTypes,
    QueryParamTypes,
    TimeoutTypes,
)

# noinspection PyProtectedMember
from httpx._utils import URLPattern
from yarl import URL

from async_pixiv.client._response import Response
from async_pixiv.client._transport import AsyncHTTPTransport, BypassAsyncHTTPTransport
from async_pixiv.error import RateLimitError
from async_pixiv.typedefs import UrlType
from async_pixiv.utils.rate_limiter import RateLimiter

try:
    from orjson import loads as default_json_loads
except ImportError:
    from json import loads as default_json_loads

__all__ = (
    "AsyncClient",
    "Retry",
)


logger = getLogger(__name__)


class Retry:
    def __init__(self, times: int = 5, sleep: float = 1):
        self.times = times
        self.sleep = sleep


class AsyncClient(DefaultAsyncClient):
    def __init__(
        self,
        *,
        limiter: RateLimiter | None = None,
        proxy: ProxyTypes | None = None,
        timeout: TimeoutTypes = None,
        trust_env: bool = True,
        bypass: bool = False,
        retry: Retry | None = None,
        json_loads: callable = default_json_loads,
    ) -> None:
        super().__init__(
            timeout=timeout,
            trust_env=trust_env,
            headers={
                "App-OS": "IOS",
                "App-OS-Version": "17.5.1",
                "App-Version": "7.20.6",
                "user-agent": "PixivAndroidApp/5.0.234 (Android 11; Pixel 5)",
                "Referer": "https://www.pixiv.net/",
                "Accept-Language": (
                    "zh-CN,zh;"
                    + "q=0.9,zh-Hans;"
                    + "q=0.8,en;"
                    + "q=0.7,zh-Hant;"
                    + "q=0.6,ja;"
                    + "q=0.5"
                ),
                "Access-Control-Expose-Headers": "Content-Length",
            },
        )

        self.limiter = limiter or RateLimiter(100, 60)
        self.retry = retry or Retry()
        self._json_loads = json_loads

        proxy_map = self._get_proxy_map(proxy, trust_env)

        # noinspection PyPep8Naming
        TransportType = (  # NOSONAR
            BypassAsyncHTTPTransport if bypass else AsyncHTTPTransport
        )

        self._transport = TransportType(
            trust_env=trust_env, json_loads=self._json_loads
        )

        # noinspection PyTypeHints
        self._mounts: dict[URLPattern, AsyncBaseTransport | None] = {
            URLPattern(key): (
                None
                if proxy is None
                else TransportType(
                    trust_env=trust_env, proxy=proxy, json_loads=self._json_loads
                )
            )
            for key, proxy in proxy_map.items()
        }
        self._mounts = dict(sorted(self._mounts.items()))

    async def _send_handling_auth(self, *args, **kwargs) -> Response:
        return await super()._send_handling_auth(*args, **kwargs)

    async def _send(self, request, *, stream, auth, follow_redirects):
        if self._state == ClientState.CLOSED:
            raise RuntimeError("Cannot send a request, as the client has been closed.")

        self._state = ClientState.OPENED
        follow_redirects = (
            self.follow_redirects
            if isinstance(follow_redirects, UseClientDefault)
            else follow_redirects
        )

        auth = self._build_request_auth(request, auth)

        response = await self._send_handling_auth(
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

    async def _send_request(
        self, request, *, stream=False, auth=USE_CLIENT_DEFAULT, follow_redirects=True
    ):
        import asyncio

        error: BaseException | None = None
        while (n := 0) < self.retry.times:
            async with self.limiter:
                try:
                    return await self._send(
                        request,
                        stream=stream,
                        auth=auth,
                        follow_redirects=follow_redirects,
                    )
                except RateLimitError:
                    logger.error(f"Rate limit. Retrying in {self.retry.sleep}s.")
                    n -= 1
                    await asyncio.sleep(self.retry.sleep)
                except Exception as exc:
                    error = exc
                    logger.warning(
                        f"Request Error: {exc or exc.__class__.__name__}. "
                        f"Will retry in {self.retry.sleep}s. ({n + 1}th retry)"
                    )
                    await asyncio.sleep(self.retry.sleep)
        if error is not None:
            raise error

    @lru_cache(64)
    def _merge_url(self, url):
        return str(
            super(AsyncClient, self)._merge_url(
                url if isinstance(url, str) else str(url)
            )
        )

    def build_request(
        self,
        method: str,
        url: URL | UrlType | str,
        *,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        **kwargs,
    ) -> Request:
        from httpx import URL as httpx_URL

        str_url = str(url)
        if isinstance(url, URL):
            yarl_url = url
            httpx_url = httpx_URL(str_url)
        elif isinstance(url, httpx_URL):
            httpx_url = url
            yarl_url = httpx_URL(str_url)
        else:
            httpx_url = httpx_URL(str_url)
            yarl_url = URL(str_url)

        headers = dict(filter(lambda x: x[1], (headers or {}).items()))
        # noinspection PyProtectedMember
        params = self._merge_queryparams(params).merge(yarl_url._parsed_query)
        return super(AsyncClient, self).build_request(
            method, httpx_url, headers=headers, params=params, **kwargs
        )

    # noinspection SpellCheckingInspection
    def _merge_queryparams(
        self, params: QueryParamTypes | None = None
    ) -> QueryParamTypes | None:
        return QueryParams(
            {
                k: v
                for k, v in dict(super()._merge_queryparams(params) or {}).items()
                if v is not None and v != ""
            }
        )
