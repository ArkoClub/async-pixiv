"""感谢 @luoshuijs"""
import logging
import ssl
from threading import Lock
from typing import Optional, TYPE_CHECKING, Tuple, Type

from httpx import (
    AsyncClient,
    AsyncHTTPTransport,
    ConnectTimeout,
    HTTPError,
    Request,
    Response,
)

try:
    import regex as re
except ImportError:
    import re

if TYPE_CHECKING:
    from types import TracebackType

__all__ = ("DNSResolver", "BypassAsyncHTTPTransport")

_DEFAULT_TIMEOUT = 5
_DEFAULT_DNS_QUERY_URLS = (
    "https://cloudflare-dns.com/dns-query",
    "https://1.0.0.1/dns-query",
    "https://1.1.1.1/dns-query",
    "https://[2606:4700:4700::1001]/dns-query",
    "https://[2606:4700:4700::1111]/dns-query",
)


# noinspection SpellCheckingInspection
class DNSResolver:
    """DNS resolver for BypassAsyncHTTPTransport."""

    _lock: Lock = Lock()
    _client: Optional[AsyncClient] = None

    @property
    def client(self) -> AsyncClient:
        with self._lock:
            if self._client is None or self._client.is_closed:
                self._client = AsyncClient()
        return self._client

    def __init__(
        self,
        dns_query_urls: Tuple[str] = _DEFAULT_DNS_QUERY_URLS,
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> None:
        self.dns_query_urls = dns_query_urls
        self.timeout = timeout
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
                logging.info(f"resolve {hostname} to {result[0]}")
                return result[0]
            except ConnectTimeout:
                pass
            except HTTPError as exc:
                exc_str = exc.__str__()
                logging.warning(
                    f"Resolve {hostname} failed with {exc.__class__}"
                    f"{(':' + exc_str) if exc_str else ''}"
                )
        return None

    async def resolve(self, request: Request) -> Request:
        host = request.url.host
        ip = await self.get(host)

        if ip:
            request.url = request.url.copy_with(host=ip)
            request.headers.setdefault("Host", host)

        return request

    async def aclose(self):
        await self._client.aclose()


# noinspection SpellCheckingInspection
class BypassAsyncHTTPTransport(AsyncHTTPTransport):
    """重写 AsyncHTTPTransport 的 handle_async_request 方法，以便在请求前解析域名。

    灵感来源于:

    https://github.com/encode/httpx/discussions/2698
    """

    def __init__(self, *args, solver: Optional[DNSResolver] = None, **kwargs) -> None:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.solver = solver or DNSResolver()
        # 注意请勿通过 AsyncClient 传入 verify 参数，因为 httpx 优先使用了 transport 的 verify 参数
        super().__init__(*args, verify=context, **kwargs)

    async def handle_async_request(self, request: Request) -> Response:
        request = await self.solver.resolve(request)
        return await super().handle_async_request(request)

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_value: Optional[BaseException] = None,
        traceback: "Optional[TracebackType]" = None,
    ) -> None:
        await self.solver.aclose()
        await super().__aexit__(exc_type, exc_value, traceback)

    async def aclose(self) -> None:
        await self.solver.aclose()
        await super().aclose()
