import logging
from functools import wraps
from io import BytesIO
from pathlib import Path
from threading import Lock as ThreadLock
from typing import (
    Any,
    Callable,
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
from arkowrapper import ArkoWrapper

# noinspection PyProtectedMember
from typing_extensions import ParamSpec

# noinspection PyProtectedMember
from async_pixiv.client._section import SectionType
from async_pixiv.error import (
    LoginError,
    OauthError,
)
from async_pixiv.model.user import Account
from async_pixiv.utils.context import set_pixiv_client
from async_pixiv.utils.net import Net
from async_pixiv.utils.singleton import Singleton

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
class PixivClient(Net, metaclass=Singleton):
    _lock: ThreadLock = ThreadLock()

    class Config(NamedTuple):
        client_id: str
        client_secret: str
        user_agent: str
        accept_language: str

    _config: Config
    _request_headers: dict[str, Any]

    access_token: str | None = None
    refresh_token: str | None = None
    account: Account | None = None
    _sections: dict[str, SectionType] = {}

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

    @property
    def accept_language(self) -> str:
        return self._headers["Accept-Language"]

    @accept_language.setter
    def accept_language(self, accept_language: str) -> None:
        self._headers.update({"Accept-Language": accept_language})

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        config_path = (Path(__file__) / "../config").resolve()
        with open(config_path, encoding="utf-8") as file:
            self._config = PixivClient.Config(
                *ArkoWrapper(file.readlines()).map(lambda x: x.strip())
            )
        self._headers.update(
            {
                "App-OS": "ios",
                "App-OS-Version": "12.2",
                "App-Version": "7.6.2",
                "user-agent": self._config.user_agent,
                "Referer": "https://www.pixiv.net/",
                "Accept-Language": self._config.accept_language,
            }
        )
        self._update_headers()

    def _update_headers(self) -> None:
        self._headers.update(
            {
                "Authorization": self.access_token
                if self.access_token is None
                else f"Bearer {self.access_token}",
            }
        )

    async def login_with_pwd(
        self, username: str, password: str, proxy: Optional[str] = None
    ) -> Account:
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
        self._update_headers()
        with set_pixiv_client(self):
            self.account = Account.model_validate(data["user"])
        return self.account

    async def login_with_token(self, token: str) -> Account:
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
        # self._update_headers()
        with set_pixiv_client(self):
            self.account = Account.model_validate(data["user"])
        return self.account

    async def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
    ) -> Account:
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
