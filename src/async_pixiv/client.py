import logging
from functools import wraps
from pathlib import Path
from typing import (
    Any,
    Callable,
    Mapping,
    NamedTuple,
    Optional,
    TYPE_CHECKING,
    Tuple,
    TypeVar,
)

from aiohttp.typedefs import (
    LooseHeaders,
    StrOrURL,
)
from typing_extensions import ParamSpec

from async_pixiv.error import (
    LoginError,
    OauthError,
)
from arkowrapper import ArkoWrapper
from async_pixiv.model import User
from async_pixiv.utils.model import Net
from async_pixiv.utils.typed import RequestMethod

if TYPE_CHECKING:
    from aiohttp import ClientResponse

__all__ = ['PixivClient']

_REDIRECT_URI = "https://app-api.pixiv.net/web/v1/users/auth/pixiv/callback"
_LOGIN_URL = "https://app-api.pixiv.net/web/v1/login"
_LOGIN_VERIFY = "https://accounts.pixiv.net/ajax/login"
_AUTH_TOKEN_URL = "https://oauth.secure.pixiv.net/auth/token"

P = ParamSpec('P')
R = TypeVar('R')
T = TypeVar('T')
logger = logging.getLogger('async_pixiv.client')


class Config(NamedTuple):
    client_id: str
    client_secret: str
    user_agent: str


class PixivClient(Net):
    _config: Config

    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user: Optional[User] = None

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
            self, *,
            limit: int = 30,
            timeout: float = 10,
            proxy: Optional[StrOrURL] = None,
            trust_env: bool = False
    ):
        super().__init__(
            limit=limit,
            timeout=timeout,
            proxy=proxy,
            trust_env=trust_env
        )
        with open(Path(__file__) / "../config", encoding='utf-8') as file:
            self._config = Config(
                *ArkoWrapper(file.readlines()).map(lambda x: x.strip())
            )

    async def _request(
            self,
            method: RequestMethod,
            url: StrOrURL, *,
            params: Optional[Mapping[str, str]] = None,
            headers: Optional[LooseHeaders] = None,
            data: Any = None,
    ) -> "ClientResponse":
        if (
                headers
                and
                not (
                        'User-Agent' in headers.keys()
                        or
                        'user-agent' in headers.keys()
                )
        ):
            headers.update({"User-Agent": self._config.user_agent})
        return await super(PixivClient, self)._request(
            method, url, params=params, headers=headers, data=data
        )

    async def login_with_pwd(self, username: str, password: str) -> User:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError("Please install 'playwright'.")

        def oauth_pkce() -> Tuple[str, str]:
            from secrets import token_urlsafe
            from hashlib import sha256
            from base64 import urlsafe_b64encode
            verifier = token_urlsafe(32)
            challenge = urlsafe_b64encode(
                sha256(verifier.encode('ascii')).digest()
            ).rstrip(b'=').decode('ascii')
            return verifier, challenge

        async with async_playwright() as playwright:
            from urllib.parse import (
                parse_qs,
                urlparse,
                urlencode,
            )
            for p in self._proxies:
                if p.scheme not in ["https", 'wss']:
                    proxy = str(p)
                    break
            # noinspection PyTypeChecker
            browser = await playwright.chromium.launch(
                proxy={"server": proxy}
            )
            context = await browser.new_context()
            api_request_context = context.request
            page = await context.new_page()

            # 访问登录页面
            code_verifier, code_challenge = oauth_pkce()
            await page.goto(urlparse(_LOGIN_URL)._replace(
                query=urlencode({
                    "code_challenge": code_challenge,
                    "code_challenge_method": "S256",
                    "client": "pixiv-android",
                })
            ).geturl(), timeout=0)

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
                raise LoginError(
                    f"登录错误，请检查登录的用户名和密码是否正确：{response['body']['errors']}"
                )
            except Exception as e:
                if not isinstance(e, LoginError):
                    logger.debug("登录成功，正尝试获取 token")

            # 获取code
            async with page.expect_request(f"{_REDIRECT_URI}*") as request:
                url = urlparse((await request.value).url)
            code = parse_qs(url.query)['code'][0]

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
                    'Accept-Encoding': 'gzip, deflate',
                    "Content-Type": 'application/x-www-form-urlencoded',
                    "User-Agent": self._config.user_agent,
                    'Host': 'oauth.secure.pixiv.net'
                },
                timeout=0
            )
            data = await response.json()
            await browser.close()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.user = User.parse_obj(data['user'])
        return self.user

    async def login_with_token(self, token: str) -> User:
        response = await self.post(
            _AUTH_TOKEN_URL, data={
                "client_id": self._config.client_id,
                "client_secret": self._config.client_secret,
                "grant_type": "refresh_token",
                "include_policy": "true",
                "refresh_token": token,
            },
            headers={"User-Agent": self._config.user_agent}
        )
        data = await response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.user = User.parse_obj(data['user'])
        return self.user

    async def login(
            self,
            username: Optional[str] = None,
            password: Optional[str] = None,
            token: Optional[str] = None
    ) -> User:
        if token is not None:
            return await self.login_with_token(token)
        else:
            return await self.login_with_pwd(username, password)
