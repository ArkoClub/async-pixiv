import typing
from contextvars import Token
from io import BytesIO

# noinspection PyProtectedMember
from httpx._client import USE_CLIENT_DEFAULT, UseClientDefault

# noinspection PyProtectedMember
from httpx._types import (
    AuthTypes,
    CookieTypes,
    HeaderTypes,
    ProxyTypes,
    RequestContent,
    RequestData,
    RequestExtensions,
    RequestFiles,
    TimeoutTypes,
    URLTypes,
)
# noinspection PyProtectedMember
from pytz.tzinfo import DstTzInfo
from yarl import URL

from async_pixiv.client._net import AsyncClient
from async_pixiv.client._response import Response

# noinspection PyProtectedMember
from async_pixiv.client.api._illust import IllustAPI

# noinspection PyProtectedMember
from async_pixiv.client.api._novel import NovelAPI

# noinspection PyProtectedMember
from async_pixiv.client.api._user import UserAPI
from async_pixiv.model.user import Account
from async_pixiv.typedefs import EnumType, ProgressHandler, StrPath
from async_pixiv.utils.rate_limiter import RateLimiter

try:
    from orjson import loads as default_json_loads
except ImportError:
    from json import loads as default_json_loads

__all__ = ("PixivClient",)

QueryParamTypes = typing.Union[QueryParamTypes, EnumType]

class PixivClientNet:
    _client: AsyncClient

    access_token: str | None = None
    refresh_token: str | None = None

    def _update_header(self, headers: HeaderTypes | None = None) -> "HeaderTypes":
        pass
    @property
    def is_closed(self) -> bool:
        pass
    async def close(self) -> None:
        pass
    async def request(
        self,
        method: str,
        url: URLTypes | URL,
        *,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        files: RequestFiles | None = None,
        json: typing.Any | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        auth: AuthTypes | UseClientDefault | None = USE_CLIENT_DEFAULT,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        extensions: RequestExtensions | None = None,
    ) -> Response:
        pass
    async def request_get(
        self,
        url: URLTypes | URL,
        *,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        auth: AuthTypes | UseClientDefault | None = USE_CLIENT_DEFAULT,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        extensions: RequestExtensions | None = None,
    ) -> Response:
        pass
    async def request_options(
        self,
        url: URLTypes | URL,
        *,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        auth: AuthTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        extensions: RequestExtensions | None = None,
    ) -> Response:
        pass
    async def request_head(
        self,
        url: URLTypes | URL,
        *,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        auth: AuthTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        extensions: RequestExtensions | None = None,
    ) -> Response:
        pass
    async def request_post(
        self,
        url: URLTypes | URL,
        *,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        files: RequestFiles | None = None,
        json: typing.Any | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        auth: AuthTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        extensions: RequestExtensions | None = None,
    ) -> Response:
        pass
    async def request_put(
        self,
        url: URLTypes | URL,
        *,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        files: RequestFiles | None = None,
        json: typing.Any | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        auth: AuthTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        extensions: RequestExtensions | None = None,
    ) -> Response:
        pass
    async def request_patch(
        self,
        url: URLTypes | URL,
        *,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        files: RequestFiles | None = None,
        json: typing.Any | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        auth: AuthTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        extensions: RequestExtensions | None = None,
    ) -> Response:
        pass
    async def request_delete(
        self,
        url: URLTypes | URL,
        *,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        auth: AuthTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
        timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        extensions: RequestExtensions | None = None,
    ) -> Response:
        pass
    async def download(
        self,
        url: URL | str,
        method: typing.Literal[
            "GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"
        ] = "GET",
        *,
        output: StrPath | BytesIO | str | None = None,
        chunk_size: int | None = None,
        progress_handler: ProgressHandler | None = None,
    ) -> bytes | StrPath | BytesIO:
        pass

class PixivClient(PixivClientNet):
    _client_token: Token[PixivClient]
    _timezone_token: Token[DstTzInfo]

    account: Account | None

    # property
    is_logged: bool

    def __init__(
        self,
        *,
        limiter: RateLimiter | None = None,
        proxy: ProxyTypes | None = None,
        timeout: TimeoutTypes = None,
        trust_env: bool = True,
        bypass: bool = False,
        retry_times: int = 5,
        retry_sleep: float = 1,
        json_loads: callable = default_json_loads,
        timezone: DstTzInfo | None = None,
    ):
        pass
    @property
    def accept_language(self) -> str:
        pass
    async def login_with_token(self, token: str | None = None) -> Account:
        pass
    async def close(self) -> None:
        pass
    USER: UserAPI
    ILLUST: IllustAPI
    NOVEL: NovelAPI
