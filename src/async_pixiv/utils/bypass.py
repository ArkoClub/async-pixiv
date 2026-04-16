"""感谢 @luoshuijs"""

import ssl
from typing import TYPE_CHECKING

from httpx import (
    AsyncHTTPTransport,
    Request,
    Response,
)

from async_pixiv.client._transport import DNSResolver

if TYPE_CHECKING:
    from types import TracebackType

__all__ = ("BypassAsyncHTTPTransport", "DNSResolver")


# noinspection SpellCheckingInspection
class BypassAsyncHTTPTransport(AsyncHTTPTransport):
    """重写 PixivAsyncHTTPTransport 的 handle_async_request 方法, 以便在请求前解析域名。

    灵感来源于:

    https://github.com/encode/httpx/discussions/2698
    """

    def __init__(self, *args, solver: DNSResolver | None = None, **kwargs) -> None:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.solver = solver or DNSResolver()
        # 注意请勿通过 AsyncClient 传入 verify 参数,
        # 因为 httpx 优先使用了 transport 的 verify 参数
        super().__init__(*args, verify=context, **kwargs)

    async def handle_async_request(self, request: Request) -> Response:
        request = await self.solver.resolve(request)
        return await super().handle_async_request(request)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: "TracebackType | None" = None,
    ) -> None:
        await self.solver.aclose()
        await super().__aexit__(exc_type, exc_value, traceback)

    async def aclose(self) -> None:
        await self.solver.aclose()
        await super().aclose()
