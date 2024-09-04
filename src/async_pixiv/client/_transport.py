import ssl
from logging import getLogger
from threading import Lock
from types import TracebackType
from typing import AsyncIterable, Iterable, Optional

import httpcore
from httpx import (
    AsyncByteStream,
    AsyncClient,
    AsyncHTTPTransport as DefaultAsyncHTTPTransport,
    HTTPTransport as DefaultHTTPTransport,
    SyncByteStream,
)

# noinspection PyProtectedMember
from httpx._transports.default import (
    AsyncResponseStream,
    ResponseStream,
    map_httpcore_exceptions,
)

from async_pixiv.client._response import Response

try:
    from orjson import loads as default_json_loads
except ImportError:
    from json import loads as default_json_loads

try:
    import regex as re
except ImportError:
    import re

__all__ = ("AsyncHTTPTransport", "BypassAsyncHTTPTransport", "HTTPTransport")


logger = getLogger(__name__)


class AsyncHTTPTransport(DefaultAsyncHTTPTransport):
    def __init__(self, *args, json_loads: callable = default_json_loads, **kwargs):
        super().__init__(*args, **kwargs)
        self._json_loads = json_loads

    async def handle_async_request(self, request) -> Response:
        assert isinstance(request.stream, AsyncByteStream)

        req = httpcore.Request(
            method=request.method,
            url=httpcore.URL(
                scheme=request.url.raw_scheme,
                host=request.url.raw_host,
                port=request.url.port,
                target=request.url.raw_path,
            ),
            headers=request.headers.raw,
            content=request.stream,
            extensions=request.extensions,
        )
        with map_httpcore_exceptions():
            resp = await self._pool.handle_async_request(req)

        assert isinstance(resp.stream, AsyncIterable)

        return Response(
            status_code=resp.status,
            headers=resp.headers,
            stream=AsyncResponseStream(resp.stream),
            extensions=resp.extensions,
            json_loads=self._json_loads,
        )


class DNSResolver:
    """DNS resolver for BypassAsyncHTTPTransport."""

    _lock: Lock = Lock()
    _client = None

    @property
    def client(self):
        with self._lock:
            if self._client is None or self._client.is_closed:
                self._client = AsyncClient()
        return self._client

    def __init__(
        self,
        dns_query_urls: tuple[str] | None = None,
        timeout: int | None = None,
    ) -> None:
        self.dns_query_urls = dns_query_urls or (
            "https://cloudflare-dns.com/dns-query",
            "https://1.0.0.1/dns-query",
            "https://1.1.1.1/dns-query",
            "https://[2606:4700:4700::1001]/dns-query",
            "https://[2606:4700:4700::1111]/dns-query",
        )
        self.timeout = timeout or 5
        self.pattern = re.compile(
            r"((\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.){3}(1\d\d|2[0-4]\d|25[0-5]|"
            r"[1-9]\d|\d)"
        )
        self.headers = {
            "accept": "application/dns-json",
        }

    async def get(self, name: str) -> Optional[str]:
        if name in [
            "app-api.pixiv.net",
            "public-api.secure.pixiv.net",
            "www.pixiv.net",
            "oauth.secure.pixiv.net",
        ]:
            # noinspection SpellCheckingInspection
            return await self.require_app_api_hosts("www.pixivision.net")
        return None

    async def require_app_api_hosts(self, hostname: str) -> Optional[str]:
        from httpx import ConnectTimeout, HTTPError

        params = {
            "ct": "application/dns-json",
            "name": hostname,
            "type": "A",
            "do": "false",
            "cd": "false",
        }
        for url in self.dns_query_urls:
            try:
                response = await self.client.get(
                    url, params=params, headers=self.headers, timeout=self.timeout
                )
                if response.is_error:
                    continue
                data = response.json()
                result = []
                for i in data["Answer"]:
                    ip = i["data"]
                    # 检查并返回 IPv4 地址
                    if self.pattern.match(ip) is not None:
                        result.append(ip)
                logger.info(f"resolve {hostname} to {result[0]}")
                return result[0]
            except ConnectTimeout:
                pass
            except HTTPError as exc:
                exc_str = exc.__str__()
                logger.warning(
                    f"Resolve {hostname} failed with {exc.__class__}"
                    f"{(':' + exc_str) if exc_str else ''}"
                )
        return None

    async def resolve[R](self, request: R) -> R:
        host = request.url.host
        ip = await self.get(host)

        if ip:
            request.url = request.url.copy_with(host=ip)
            request.headers.setdefault("Host", host)

        return request

    async def aclose(self):
        await self._client.aclose()


class BypassAsyncHTTPTransport(AsyncHTTPTransport):
    def __init__(self, *args, solver: DNSResolver | None = None, **kwargs) -> None:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.solver = solver or DNSResolver()
        # 注意请勿通过 AsyncClient 传入 verify 参数，因为 httpx 优先使用了 transport 的 verify 参数
        super().__init__(*args, verify=context, **kwargs)

    async def handle_async_request(self, request) -> Response:
        request = await self.solver.resolve(request)
        return await super().handle_async_request(request)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        await self.solver.aclose()
        await super().__aexit__(exc_type, exc_value, traceback)

    async def aclose(self) -> None:
        await self.solver.aclose()
        await super().aclose()


class HTTPTransport(DefaultHTTPTransport):
    # noinspection PyProtectedMember
    def handle_request(self, request):
        assert isinstance(request.stream, SyncByteStream)

        req = httpcore.Request(
            method=request.method,
            url=httpcore.URL(
                scheme=request.url.raw_scheme,
                host=request.url.raw_host,
                port=request.url.port,
                target=request.url.raw_path,
            ),
            headers=request.headers.raw,
            content=request.stream,
            extensions=request.extensions,
        )
        with map_httpcore_exceptions():
            resp = self._pool.handle_request(req)

        assert isinstance(resp.stream, Iterable)

        return Response(
            status_code=resp.status,
            headers=resp.headers,
            stream=ResponseStream(resp.stream),
            extensions=resp.extensions,
        )
