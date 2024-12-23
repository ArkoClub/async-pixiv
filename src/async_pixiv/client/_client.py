import os
from functools import cached_property, partial
from io import BytesIO
from typing import Literal, TYPE_CHECKING

# noinspection PyProtectedMember
from pytz.tzinfo import DstTzInfo

from async_pixiv.client._net import AsyncClient, Retry
from async_pixiv.model.user import Account
from async_pixiv.utils.context import PixivClientContext, TimezoneContext

try:
    from orjson import loads as default_json_loads
except ImportError:
    from json import loads as default_json_loads

if TYPE_CHECKING:
    from pathlib import Path

    # noinspection PyProtectedMember
    from async_pixiv.client.api._abc import APIBase

    # noinspection PyProtectedMember
    from async_pixiv.client.api._user import UserAPI

    # noinspection PyProtectedMember
    from async_pixiv.client.api._illust import IllustAPI

    # noinspection PyProtectedMember
    from async_pixiv.client.api._novel import NovelAPI


__all__ = ("PixivClient",)

# noinspection SpellCheckingInspection
PIXIV_APP_CLIENT_ID = "MOBrBDS8blbauoSck0ZfDbtuzpyT"
# noinspection SpellCheckingInspection
PIXIV_APP_CLIENT_SECRET = "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj"


class PixivClientNet:
    _client: AsyncClient

    access_token: str | None = None
    refresh_token: str | None = None

    @property
    def is_closed(self) -> bool:
        return self._client.is_closed

    async def close(self) -> None:
        await self._client.aclose()

    def _update_header(self, headers=None):
        return (headers or {}) | {
            "Authorization": (
                self.access_token
                if self.access_token is None
                else f"Bearer {self.access_token}"
            ),
        }

    async def request(self, *args, headers=None, **kwargs):
        return await self._client.request(
            *args, headers=self._update_header(headers), **kwargs
        )

    async def request_get(self, *args, headers=None, **kwargs):
        return await self._client.get(
            *args, headers=self._update_header(headers), **kwargs
        )

    async def request_options(self, *args, headers=None, **kwargs):
        return await self._client.options(
            *args, headers=self._update_header(headers), **kwargs
        )

    async def request_head(self, *args, headers=None, **kwargs):
        return await self._client.head(
            *args, headers=self._update_header(headers), **kwargs
        )

    async def request_post(self, *args, headers=None, **kwargs):
        return await self._client.post(
            *args, headers=self._update_header(headers), **kwargs
        )

    async def request_put(self, *args, headers=None, **kwargs):
        return await self._client.put(
            *args, headers=self._update_header(headers), **kwargs
        )

    async def request_patch(self, *args, headers=None, **kwargs):
        return await self._client.patch(
            *args, headers=self._update_header(headers), **kwargs
        )

    async def request_delete(self, *args, headers=None, **kwargs):
        return await self._client.delete(
            *args, headers=self._update_header(headers), **kwargs
        )

    async def download(self, url, method="GET", *, output=None, chunk_size=None):
        async with self._client.stream(
            method, url, headers=self._update_header()
        ) as response:
            from async_pixiv.utils.overwrite import Response

            response: Response
            if output is None:
                data = b""
                async for chunk in response.aiter_bytes(chunk_size):
                    data += chunk
                return data
            elif not isinstance(output, BytesIO):
                from aiofiles import open as async_open

                output = Path(output).resolve()

                async with async_open(output, mode="wb") as file:
                    async for chunk in response.aiter_bytes(chunk_size):
                        await file.write(chunk)
            else:
                async for chunk in response.aiter_bytes(chunk_size):
                    # noinspection PyTypeChecker
                    output.write(chunk)
        return output


# noinspection PyPropertyDefinition
class PixivClient(PixivClientNet):
    account = None

    @property
    def is_logged(self) -> bool:
        return self.refresh_token is not None

    @property
    def accept_language(self) -> str:
        return self._client.headers["Accept-Language"]

    @accept_language.setter
    def accept_language(self, accept_language: str) -> None:
        self._client.headers.update({"Accept-Language": accept_language})

    def __init__(
        self,
        *,
        limiter=None,
        proxy=None,
        timeout=None,
        trust_env=True,
        bypass=False,
        retry_times=5,
        retry_sleep=1,
        json_loads=default_json_loads,
        timezone: DstTzInfo | None = None,
    ):
        self._sections = {}
        self._client = AsyncClient(
            limiter=limiter,
            proxy=proxy,
            timeout=timeout,
            trust_env=trust_env,
            bypass=bypass,
            json_loads=json_loads,
            retry=Retry(times=retry_times, sleep=retry_sleep),
        )
        self._client_token = PixivClientContext.set(self)
        self._timezone_token = TimezoneContext.set(timezone)

    async def login_with_token(self, token=None) -> Account:
        if token is None:
            token = os.environ["PIXIV_TOKEN"]

        response = await self.request_post(
            "https://oauth.secure.pixiv.net/auth/token",
            data={
                "client_id": PIXIV_APP_CLIENT_ID,
                "client_secret": PIXIV_APP_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "include_policy": "true",
                "refresh_token": token,
            },
        )
        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.account = Account.model_validate(data["user"])

        return self.account

    async def close(self) -> None:
        PixivClientContext.reset(self._client_token)
        TimezoneContext.reset(self._timezone_token)
        await super().close()

    def _get_section(
        self, section_type: Literal["User", "Illust", "Novel", "Manga"]
    ) -> "APIBase":
        section = self._sections.get(section_type, None)
        if section is None:
            api_type_name = f"{section_type}API"
            exec(
                f"from async_pixiv.client.api._{section_type.lower()} "
                + f"import {api_type_name}"
            )
            api_type: type["APIBase"] = eval(api_type_name)
            self._sections[section_type] = api_type(self)
        return self._sections[section_type]

    USER: "UserAPI" = cached_property(partial(_get_section, section_type="User"))
    ILLUST: "IllustAPI" = cached_property(partial(_get_section, section_type="Illust"))
    NOVEL: "NovelAPI" = cached_property(partial(_get_section, section_type="Novel"))
