from __future__ import annotations

import asyncio
import os
from inspect import isawaitable
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

    @staticmethod
    def _prepare_output_path(output, url) -> Path:
        output_path = Path(output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not output_path.suffix:
            output_path = output_path.with_suffix(Path(str(url)).suffix)
        return output_path

    @staticmethod
    async def _download_to_bytes(response, chunk_size, add_progress):
        data = bytearray()
        uploaded = 0
        async for chunk in response.aiter_bytes(chunk_size):
            data.extend(chunk)
            uploaded += len(chunk)
            add_progress(uploaded)
        return bytes(data)

    @staticmethod
    async def _download_to_path(
        response, output_path, chunk_size, add_progress
    ) -> None:
        from aiofiles import open as async_open

        async with async_open(output_path, mode="wb") as file:
            uploaded = 0
            async for chunk in response.aiter_bytes(chunk_size):
                await file.write(chunk)
                uploaded += len(chunk)
                add_progress(uploaded)

    @staticmethod
    async def _download_to_buffer(response, output, chunk_size, add_progress):
        uploaded = 0
        async for chunk in response.aiter_bytes(chunk_size):
            # noinspection PyTypeChecker
            output.write(chunk)
            uploaded += len(chunk)
            add_progress(uploaded)
        return output

    async def download(
        self, url, method="GET", *, output=None, chunk_size=None, progress_handler=None
    ):
        _background_tasks = set()

        async def handle_progress(_uploaded, _total, _progress_handler):
            if _progress_handler is None:
                return
            result = _progress_handler(_uploaded, _total)
            if isawaitable(result):
                await result

        def add_handle_progress_task(_uploaded, _total):
            task = asyncio.create_task(
                handle_progress(_uploaded, _total, progress_handler)
            )
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)

        async def finish_progress_tasks():
            if _background_tasks:
                await asyncio.gather(*tuple(_background_tasks))

        chunk_size = chunk_size or 2**20
        async with self._client.stream(
            method, url, headers=self._update_header()
        ) as response:
            response: Response
            response.raise_for_status().raise_for_status()

            total = int(response.headers.get("content-length", 0))

            def add_progress(uploaded):
                add_handle_progress_task(uploaded, total)

            if output is None:
                data = await self._download_to_bytes(response, chunk_size, add_progress)
                await finish_progress_tasks()
                return data

            if isinstance(output, BytesIO):
                data = await self._download_to_buffer(
                    response,
                    output,
                    chunk_size,
                    add_progress,
                )
                await finish_progress_tasks()
                return data

            output_path = self._prepare_output_path(output, url)
            await self._download_to_path(
                response,
                output_path,
                chunk_size,
                add_progress,
            )
            await finish_progress_tasks()
            return output_path


# noinspection PyPropertyDefinition
class PixivClient(PixivClientNet):
    account: Account | None = None
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

    async def login_with_token(self, token: str | None = None) -> Account:
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
        self.account = Account.model_validate(data["user"], _pixiv_client=self)

        return self.account

    async def close(self) -> None:
        await super().close()
