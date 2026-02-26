import asyncio
import os
from inspect import iscoroutinefunction
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

import tzlocal

from async_pixiv._compat import json_loads as default_json_loads
from async_pixiv.client._net import AsyncClient, Retry
from async_pixiv.client.api import IllustAPI, NovelAPI, UserAPI
from async_pixiv.model.user import Account

# noinspection PyProtectedMember
if TYPE_CHECKING:
    from async_pixiv.utils.overwrite import Response


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

    async def request(self, method: str, *args, headers=None, **kwargs):
        return await self._client.request(
            method,
            *args,
            headers=self._update_header(headers),
            **kwargs,
        )

    async def request_get(self, *args, headers=None, **kwargs):
        return await self.request("GET", *args, headers=headers, **kwargs)

    async def request_options(self, *args, headers=None, **kwargs):
        return await self.request("OPTIONS", *args, headers=headers, **kwargs)

    async def request_head(self, *args, headers=None, **kwargs):
        return await self.request("HEAD", *args, headers=headers, **kwargs)

    async def request_post(self, *args, headers=None, **kwargs):
        return await self.request("POST", *args, headers=headers, **kwargs)

    async def request_put(self, *args, headers=None, **kwargs):
        return await self.request("PUT", *args, headers=headers, **kwargs)

    async def request_patch(self, *args, headers=None, **kwargs):
        return await self.request("PATCH", *args, headers=headers, **kwargs)

    async def request_delete(self, *args, headers=None, **kwargs):
        return await self.request("DELETE", *args, headers=headers, **kwargs)

    async def download(
        self, url, method="GET", *, output=None, chunk_size=None, progress_handler=None
    ):
        _background_tasks = set()

        async def handle_progress(_uploaded, _total, _progress_handler):
            if _progress_handler is None:
                return
            if iscoroutinefunction(_progress_handler):
                await _progress_handler(_uploaded, _total)
            else:
                _progress_handler(_uploaded, _total)

        def add_handle_progress_task(_uploaded, _total):
            task = asyncio.create_task(
                handle_progress(_uploaded, _total, progress_handler)
            )
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)

        chunk_size = chunk_size or 2**20
        async with self._client.stream(
            method, url, headers=self._update_header()
        ) as response:
            response: Response
            response.raise_for_status().raise_for_status()

            total = int(response.headers.get("content-length", 0))
            if output is None:
                data = b""
                async for chunk in response.aiter_bytes(chunk_size):
                    data += chunk
                    add_handle_progress_task(len(data), total)
                return data
            elif not isinstance(output, BytesIO):  # str or Path
                from aiofiles import open as async_open

                output = Path(output).resolve()
                output.parent.mkdir(parents=True, exist_ok=True)
                if not output.suffix:
                    output = output.with_suffix(Path(str(url)).suffix)
                async with async_open(output, mode="wb") as file:
                    uploaded = 0
                    async for chunk in response.aiter_bytes(chunk_size):
                        await file.write(chunk)
                        uploaded += len(chunk)
                        add_handle_progress_task(uploaded, total)
            else:  # BytesIO
                uploaded = 0
                async for chunk in response.aiter_bytes(chunk_size):
                    # noinspection PyTypeChecker
                    output.write(chunk)
                    uploaded += len(chunk)
                    add_handle_progress_task(uploaded, total)
        return output


# noinspection PyPropertyDefinition
class PixivClient(PixivClientNet):
    account = None
    USER: UserAPI
    ILLUST: IllustAPI
    NOVEL: NovelAPI

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
        timezone=None,
    ):
        self._client = AsyncClient(
            limiter=limiter,
            proxy=proxy,
            timeout=timeout,
            trust_env=trust_env,
            bypass=bypass,
            json_loads=json_loads,
            retry=Retry(times=retry_times, sleep=retry_sleep),
        )
        self.USER = UserAPI(self)
        self.ILLUST = IllustAPI(self)
        self.NOVEL = NovelAPI(self)
        self.timezone = timezone or tzlocal.get_localzone()

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
        await super().close()
