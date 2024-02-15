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
from async_pixiv.utils.func import oauth_pkce
from async_pixiv.utils.net import Net
from async_pixiv.utils.singleton import Singleton

if TYPE_CHECKING:
    from async_pixiv.client import (
        USER,
        ILLUST,
        NOVEL,
    )

__all__ = ["PixivClient"]

_REDIRECT_URL = "https://app-api.pixiv.net/web/v1/users/auth/pixiv/callback"
_LOGIN_URL = "https://app-api.pixiv.net/web/v1/login"
_LOGIN_VERIFY = "https://accounts.pixiv.net/ajax/login"
_LOGIN_TWO_FACTOR = "https://accounts.pixiv.net/ajax/login/two-factor-authentication"
_AUTH_TOKEN_URL = "https://oauth.secure.pixiv.net/auth/token"

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")
logger = logging.getLogger("async_pixiv.client")


# noinspection PyTypeChecker,PyPep8Naming
class _PixivClientSections:
    _lock: ThreadLock = ThreadLock()
    _sections: dict[str, SectionType] = {}

    @property
    def USER(self) -> "USER":  # NOSONAR
        with self._lock:
            if self._sections.get("user", None) is None:
                from async_pixiv.client import USER

                self._sections["user"] = USER(self)
        return self._sections["user"]

    @property
    def ILLUST(self) -> "ILLUST":  # NOSONAR
        with self._lock:
            if self._sections.get("illust", None) is None:
                from async_pixiv.client import ILLUST

                self._sections["illust"] = ILLUST(self)
        return self._sections["illust"]

    @property
    def NOVEL(self) -> "NOVEL":  # NOSONAR
        with self._lock:
            if self._sections.get("novel", None) is None:
                from async_pixiv.client import NOVEL

                self._sections["novel"] = NOVEL(self)
        return self._sections["novel"]


# noinspection PyPep8Naming
class PixivClient(Net, _PixivClientSections, metaclass=Singleton):
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
                "Authorization": (
                    self.access_token
                    if self.access_token is None
                    else f"Bearer {self.access_token}"
                ),
            }
        )

    async def login_with_pwd(  # NOSONAR
        self,
        username: str,
        password: str,
        one_time_password_secret: Optional[str] = None,
        *,
        proxy: Optional[str] = None,
    ) -> Account:
        try:
            from playwright.async_api import async_playwright

            # noinspection PyProtectedMember
            from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError

        except ImportError:
            raise ImportError("Please install 'playwright'.")
        try:
            from pyotp.totp import TOTP
        except ImportError:
            raise ImportError("Please install 'pyotp'.")
        from urllib.parse import parse_qs, urlparse, urlencode

        if one_time_password_secret is not None:
            totp = TOTP(one_time_password_secret)
        else:
            totp = None

        playwright_context = async_playwright()
        playwright = await playwright_context.__aenter__()

        if proxy is not None:
            browser = await playwright.firefox.launch(proxy={"server": proxy})
        else:
            browser = await playwright.firefox.launch()

        context = await browser.new_context()
        api_request_context = context.request
        page = await context.new_page()

        async def raise_errors(_response) -> None:
            if errors := _response["body"].get("errors"):
                logger.debug(f"登录错误：{errors}")
                info_box = page.locator("form > p")
                if not (await info_box.count()):
                    info_box = page.locator("form > div:first-child")
                information = await info_box.inner_text()
                raise LoginError(information or "请检查输入的信息是否正确")

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
        await page.locator('input[autocomplete="username"]').fill(username)
        await page.locator('input[type="password"]').fill(password)

        submit_button = page.locator("form:has(fieldset) button[type='submit']")

        # 验证登录
        try:
            async with page.expect_response(_LOGIN_VERIFY + "*") as future_response:
                await submit_button.click()
                response = await (await future_response.value).json()
        except PlaywrightTimeoutError:
            raise TimeoutError("登录超时")

        await raise_errors(response)

        # 获取 code
        if response["body"].get("requireTwoFactorAuthentication"):
            ont_time_code_input = page.locator('input[autocomplete="one-time-code"]')
            await ont_time_code_input.fill(
                totp.now()
                if totp
                else input("由于您开启了两步验证，现请输入两步验证的验证码：")
            )

            async with page.expect_request(_REDIRECT_URL + "*") as request:
                try:
                    async with (
                        page.expect_response(
                            _LOGIN_TWO_FACTOR + "*", timeout=3000
                        ) as future,
                    ):
                        await submit_button.click()
                        response = await (await future.value).json()
                    await raise_errors(response)
                except PlaywrightTimeoutError:
                    logger.debug("两步验证成功")
                url = urlparse((await request.value).url)
        else:
            async with page.expect_request(_REDIRECT_URL + "*") as request:
                url = urlparse((await request.value).url)

        code = parse_qs(url.query)["code"][0]

        logger.debug("登录成功，正尝试获取 token")

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
                "redirect_uri": _REDIRECT_URL,
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
        await playwright_context.__aexit__()

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
        self._update_headers()
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
        # noinspection PyArgumentList
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
