"""重写 telegram.request.HTTPXRequest 使其使用 ujson 库进行 json 序列化"""
from typing import Any, AsyncIterable, Iterable

import httpcore
from httpx import (
    AsyncByteStream,
    AsyncHTTPTransport as DefaultAsyncHTTPTransport,
    HTTPTransport as DefaultHTTPTransport,
    Request,
    Response as DefaultResponse,
    SyncByteStream,
)

# noinspection PyProtectedMember
from httpx._transports.default import (
    AsyncResponseStream,
    ResponseStream,
    map_httpcore_exceptions,
)

from async_pixiv.error import ApiError, NotExist, RateLimit

try:
    import ujson as jsonlib
except ImportError:
    import json as jsonlib

__all__ = ("AsyncHTTPTransport", "HTTPTransport", "Response")

STATUS_ERROR_MAP = {
    404: NotExist,
}
RESULT_ERROR_MAP = {
    "Rate Limit": RateLimit,
}


class Response(DefaultResponse):
    def raise_for_status(self) -> None:
        if self.status_code != 200:
            if (error := STATUS_ERROR_MAP.get(self.status_code)) is not None:
                raise error(self)
            else:
                super().raise_for_status()

    # noinspection PyMethodMayBeStatic
    def raise_for_result(self, result: dict) -> None:
        if (error := result.get("error")) is not None and error:
            raise RESULT_ERROR_MAP.get(error["reason"], ApiError)(error)

    def json(
        self,
        raise_for_result: bool = True,
        raise_for_status: bool = True,
        **kwargs: Any,
    ) -> Any:
        if raise_for_status:
            self.raise_for_status()

        result = jsonlib.loads(self.text, **kwargs)

        if isinstance(result, dict) and raise_for_result:
            self.raise_for_result(result)

        return result


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
