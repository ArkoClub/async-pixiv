import logging
from functools import wraps
from io import BytesIO
from pathlib import Path
from threading import Lock as ThreadLock
from typing import (
    Any,
    AsyncIterator,
    Callable,
    ClassVar,
    Dict,
    List,
    NamedTuple,
    Optional,
    TYPE_CHECKING,
    Tuple,
    TypeVar,
    Union,
)

from aiofiles import open as async_open

# noinspection PyUnresolvedReferences
from aiofiles.tempfile import SpooledTemporaryFile
from aiohttp.typedefs import StrOrURL
from aiolimiter import AsyncLimiter
from arkowrapper import ArkoWrapper
from httpx import USE_CLIENT_DEFAULT

# noinspection PyProtectedMember
from httpx._client import UseClientDefault

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
from typing_extensions import ParamSpec

# noinspection PyProtectedMember
from async_pixiv.client._section import SectionType
from async_pixiv.error import (
    LoginError,
    OauthError,
)
from async_pixiv.model.user import User
from async_pixiv.utils.context import set_pixiv_client
from async_pixiv.utils.net import Net
from async_pixiv.utils.overwrite import Response

if TYPE_CHECKING:
    from async_pixiv.client import (
        USER,
        ILLUST,
        NOVEL,
    )

__all__ = ["PixivClient"]

_REDIRECT_URI = "https://app-api.pixiv.net/web/v1/users/auth/pixiv/callback"
_LOGIN_URL = "https://app-api.pixiv.net/web/v1/login"
_LOGIN_VERIFY = "https://accounts.pixiv.net/ajax/login"
_AUTH_TOKEN_URL = "https://oauth.secure.pixiv.net/auth/token"

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")
logger = logging.getLogger("async_pixiv.client")


# noinspection PyPep8Naming
class PixivClient(Net):
    _instances: ClassVar[List["PixivClient"]] = []

    @classmethod
    def get_client(cls) -> "PixivClient":
        if cls._instances:
            return cls._instances[0]
        else:
            raise ValueError("请先实列化一个 PixivClient ")

    @classmethod
    def get_clients(cls) -> List["PixivClient"]:
        return cls._instances

    _lock: ThreadLock = ThreadLock()

    class Config(NamedTuple):
        client_id: str
        client_secret: str
        user_agent: str
        accept_language: str

    _config: Config
    _request_headers: Dict[str, Any]

    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    account: Optional[User] = None
    _sections: Dict[str, SectionType] = {}

    @property
    def USER(self) -> "USER":
        with self._lock:
            if self._sections.get("user", None) is None:
                from async_pixiv.client import USER

                self._sections["user"] = USER(self)
        return self._sections["user"]

    @property
    def ILLUST(self) -> "ILLUST":
        with self._lock:
            if self._sections.get("illust", None) is None:
                from async_pixiv.client import ILLUST

                self._sections["illust"] = ILLUST(self)
        return self._sections["illust"]

    @property
    def NOVEL(self) -> "NOVEL":
        with self._lock:
            if self._sections.get("novel", None) is None:
                from async_pixiv.client import NOVEL

                self._sections["novel"] = NOVEL(self)
        return self._sections["novel"]

    @property
    def is_logged(self) -> bool:
        return self.refresh_token is not None

    def need_logged(self, func: Callable[[P], R]) -> Callable[[P], R]:
        @wraps(func)
        def wrapper():
            if not self.is_logged:
                raise OauthError("Please login.")
            return func

        return wrapper

    def __init__(
        self,
        *,
        max_rate: float = 100,
        rate_time_period: float = 60,
        timeout: float = 10,
        proxies: Optional[ProxiesTypes] = None,
        trust_env: bool = False,
        retry: int = 5,
        retry_sleep: float = 1,
    ):
        super().__init__(
            rate_limiter=AsyncLimiter(max_rate, rate_time_period),
            timeout=timeout,
            proxies=proxies,
            trust_env=trust_env,
            retry=retry,
            retry_sleep=retry_sleep,
        )
        config_path = (Path(__file__) / "../config").resolve()
        with open(config_path, encoding="utf-8") as file:
            self._config = PixivClient.Config(
                *ArkoWrapper(file.readlines()).map(lambda x: x.strip())
            )
        self._request_headers = {
            "App-OS": "ios",
            "App-OS-Version": "12.2",
            "App-Version": "7.6.2",
            "user-agent": self._config.user_agent,
            "Referer": "https://app-api.pixiv.net/",
            "Accept-Language": "zh-CN,zh;q=0.9,zh-Hans;q=0.8,en;q=0.7,zh-Hant;"
            "q=0.6,ja;q=0.5",
        }
        PixivClient._instances.append(self)

    def set_accept_language(self, language: str) -> None:
        self._request_headers.update({"Accept-Language": language})

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
        headers = headers or {}
        params = params or {}

        headers.update(
            {
                "Authorization": self.access_token
                if self.access_token is None
                else f"Bearer {self.access_token}",
            }
        )

        for key, value in self._request_headers.items():
            if key not in headers:
                headers[key] = value

        return await super().request(
            method,
            str(url),
            content=content,
            data=data,
            files=files,
            json=json,
            params={k: v for k, v in params.items() if v is not None},
            headers={k: v for k, v in headers.items() if v is not None},
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )

    def stream(
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
        headers = headers or {}
        params = params or {}

        headers.update(
            {
                "Authorization": self.access_token
                if self.access_token is None
                else f"Bearer {self.access_token}",
                **self._request_headers,
            }
        )

        return super().stream(
            method,
            str(url),
            content=content,
            data=data,
            files=files,
            json=json,
            params={k: v for k, v in params.items() if v is not None},
            headers={k: v for k, v in headers.items() if v is not None},
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )

    async def login_with_pwd(
        self, username: str, password: str, proxy: Optional[str] = None
    ) -> User:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError("Please install 'playwright'.")

        def oauth_pkce() -> Tuple[str, str]:
            from secrets import token_urlsafe
            from hashlib import sha256
            from base64 import urlsafe_b64encode

            verifier = token_urlsafe(32)
            challenge = (
                urlsafe_b64encode(sha256(verifier.encode("ascii")).digest())
                .rstrip(b"=")
                .decode("ascii")
            )
            return verifier, challenge

        async with async_playwright() as playwright:
            from urllib.parse import (
                parse_qs,
                urlparse,
                urlencode,
            )

            if proxy is not None:
                # noinspection PyTypeChecker
                browser = await playwright.chromium.launch(proxy={"server": proxy})
            else:
                browser = await playwright.chromium.launch()
            context = await browser.new_context()
            api_request_context = context.request
            page = await context.new_page()

            # 访问登录页面
            code_verifier, code_challenge = oauth_pkce()
            await page.goto(
                urlparse(_LOGIN_URL)
                ._replace(
                    query=urlencode(
                        {
                            "code_challenge": code_challenge,
                            "code_challenge_method": "S256",
                            "client": "pixiv-android",
                        }
                    )
                )
                .geturl(),
                timeout=0,
            )

            # 输入用户名与密码
            await page.locator(".degQSE").fill(username)
            await page.locator(".hfoSmp").fill(password)

            # 点击登录按钮
            # noinspection SpellCheckingInspection
            await page.locator("button.sc-bdnxRM:nth-child(5)").click()

            # 验证登录
            # noinspection PyBroadException
            try:
                async with page.expect_response(f"{_LOGIN_VERIFY}*") as future:
                    response = await (await future.value).json()
                raise LoginError(f"登录错误，请检查登录的用户名和密码是否正确：{response['body']['errors']}")
            except Exception as e:
                if not isinstance(e, LoginError):
                    logger.debug("登录成功，正尝试获取 token")

            # 获取code
            async with page.expect_request(f"{_REDIRECT_URI}*") as request:
                url = urlparse((await request.value).url)
            code = parse_qs(url.query)["code"][0]

            # 获取token
            response = await api_request_context.post(
                _AUTH_TOKEN_URL,
                form={
                    "client_id": self._config.client_id,
                    "client_secret": self._config.client_secret,
                    "code": code,
                    "code_verifier": code_verifier,
                    "grant_type": "authorization_code",
                    "include_policy": "true",
                    "redirect_uri": _REDIRECT_URI,
                },
                headers={
                    "Accept-Encoding": "gzip, deflate",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": self._config.user_agent,
                    "Host": "oauth.secure.pixiv.net",
                },
                timeout=0,
            )
            data = await response.json()
            await browser.close()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        with set_pixiv_client(self):
            self.account = User.parse_obj(data["user"])
        return self.account

    async def login_with_token(self, token: str) -> User:
        response = await self.post(
            _AUTH_TOKEN_URL,
            data={
                "client_id": self._config.client_id,
                "client_secret": self._config.client_secret,
                "grant_type": "refresh_token",
                "include_policy": "true",
                "refresh_token": token,
            },
            headers={"User-Agent": self._config.user_agent},
        )
        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        with set_pixiv_client(self):
            self.account = User.parse_obj(data["user"])
        return self.account

    async def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
    ) -> User:
        if token is not None:
            return await self.login_with_token(token)
        else:
            return await self.login_with_pwd(username, password)

    async def download(
        self,
        url: StrOrURL,
        *,
        output: Optional[Union[str, Path, BytesIO]] = None,
        chunk_size: Optional[int] = None,
    ) -> bytes:
        data = b""
        async with self.stream("GET", url) as response:
            if not isinstance(output, BytesIO) and output:
                output = Path(output).resolve()

                async with async_open(output) as file:
                    async for chunk in response.aiter_bytes(chunk_size):
                        data += chunk
                        await file.write(chunk)
            else:
                async for chunk in response.aiter_bytes(chunk_size):
                    data += chunk
        return data
