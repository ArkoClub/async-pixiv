from typing import Any, AsyncIterable, Iterable, Self

import httpcore
from httpx import (
    AsyncByteStream,
    AsyncClient as DefaultAsyncClient,
    AsyncHTTPTransport as DefaultAsyncHTTPTransport,
    HTTPTransport as DefaultHTTPTransport,
    Request,
    Response as DefaultResponse,
    SyncByteStream,
)
from functools import lru_cache

# noinspection PyProtectedMember
from httpx._transports.default import (
    AsyncResponseStream,
    ResponseStream,
    map_httpcore_exceptions,
)

from async_pixiv.error import (
    APIError,
    InvalidRefreshToken,
    NotExistError,
    PixivError,
    RateLimitError,
)

try:
    from orjson import loads as json_loads
except ImportError:
    from json import loads as json_loads

__all__ = ("AsyncHTTPTransport", "HTTPTransport", "Response", "AsyncClient")

STATUS_ERROR_MAP = {
    404: NotExistError,
}
RESULT_ERROR_MAP = {
    "Rate Limit": RateLimitError,
    "invalid_grant": InvalidRefreshToken,
}


class Response(DefaultResponse):
    _json_data: dict[str, Any] | None = None

    def raise_for_status(self) -> Self:
        if self.status_code != 200:
            if (error := STATUS_ERROR_MAP.get(self.status_code)) is not None:
                raise error(self)
            else:
                super().raise_for_status()
        return self

    # noinspection PyMethodMayBeStatic
    def raise_for_result(self) -> Self:
        if (json_data := self.json()) is not None:
            if (errors := json_data.get("errors")) is not None and errors:
                raise PixivError(errors)
            elif (error := json_data.get("error")) is not None and error:
                raise RESULT_ERROR_MAP.get(error["message"], APIError)(error)
        return self

    @lru_cache(maxsize=8)
    def json(self, **kwargs: Any) -> dict[str, Any]:
        if self._json_data is None:
            self._json_data = json_loads(self.content, **kwargs)
        return self._json_data


# noinspection PyProtectedMember
class AsyncHTTPTransport(DefaultAsyncHTTPTransport):
    async def handle_async_request(self, request: Request) -> Response:
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
        )


class HTTPTransport(DefaultHTTPTransport):
    # noinspection PyProtectedMember
    def handle_request(self, request: Request) -> Response:
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


class AsyncClient(DefaultAsyncClient):
    async def _send_handling_auth(
        self, request, auth, follow_redirects, history
    ) -> Response:
        return await super()._send_handling_auth(
            request, auth, follow_redirects, history
        )
