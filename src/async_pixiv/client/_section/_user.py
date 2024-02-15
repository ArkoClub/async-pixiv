from typing import Sequence

from async_pixiv.client._section._base import (
    SearchFilter,
    SearchShort,
    V1_API,
    _Section,
)
from async_pixiv.model.illust import IllustType
from async_pixiv.model.result import (
    UserBookmarksIllustsResult,
    UserDetailResult,
    UserIllustsResult,
    UserNovelsResult,
    UserRelatedResult,
    UserSearchResult,
)
from async_pixiv.typedefs import DurationTypes, FilterTypes, IllustTypes, ShortTypes
from async_pixiv.utils.context import set_pixiv_client

__all__ = ("USER",)


# noinspection PyShadowingBuiltins
class USER(_Section):
    async def search(
        self,
        words: str | Sequence[str],
        *,
        sort: ShortTypes = SearchShort.DateDecrease,
        duration: DurationTypes | None = None,
        filter: FilterTypes | None = SearchFilter.ios,
        offset: int | None = None,
        **kwargs,
    ) -> UserSearchResult:
        data = await self._search(
            words=words,
            sort=sort,
            duration=duration,
            filter=filter,
            offset=offset,
            **kwargs,
        )
        with set_pixiv_client(self._pixiv_client):
            return UserSearchResult.model_validate(data)

    async def detail(
        self,
        id: int | None = None,
        *,
        filter: FilterTypes | None = SearchFilter.ios,
    ) -> UserDetailResult:
        data = await self._detail(
            id=self._pixiv_client.account.id if id is None else id, filter=filter
        )
        with set_pixiv_client(self._pixiv_client):
            return UserDetailResult.model_validate(data)

    async def illusts(
        self,
        id: int | None = None,
        *,
        type: IllustTypes = IllustType.illust,
        filter: FilterTypes = SearchFilter.ios,
        offset: int | None = None,
    ) -> UserIllustsResult:
        data = (
            await self._pixiv_client.get(
                V1_API / "user/illusts",
                params={
                    "user_id": self._pixiv_client.account.id if id is None else id,
                    "type": type,
                    "filter": filter,
                    "offset": offset,
                },
            )
        ).json()
        with set_pixiv_client(self._pixiv_client):
            return UserIllustsResult.model_validate(data)

    async def bookmarks(
        self,
        id: int | None = None,
        *,
        tag: str | None = None,
        max_bookmark_id: int | None = None,
        filter: FilterTypes = SearchFilter.ios,
    ) -> UserBookmarksIllustsResult:
        data = (
            await self._pixiv_client.get(
                V1_API / "user/bookmarks/illust",
                params={
                    "user_id": self._pixiv_client.account.id if id is None else id,
                    "filter": filter,
                    "tag": tag,
                    "max_bookmark_id": max_bookmark_id,
                    "restrict": "public",
                },
            )
        ).json()
        with set_pixiv_client(self._pixiv_client):
            return UserBookmarksIllustsResult.model_validate(data)

    async def novels(
        self,
        id: int | None = None,
        *,
        filter: FilterTypes = SearchFilter.ios,
        offset: int = None,
    ) -> UserNovelsResult:
        data = (
            await self._pixiv_client.get(
                V1_API / "user/novels",
                params={
                    "user_id": self._pixiv_client.account.id if id is None else id,
                    "filter": filter,
                    "offset": offset,
                },
            )
        ).json()
        with set_pixiv_client(self._pixiv_client):
            return UserNovelsResult.model_validate(data)

    async def related(
        self,
        id: int | None = None,
        *,
        filter: FilterTypes = SearchFilter.ios,
        offset: int = None,
    ) -> UserRelatedResult:
        data = (
            await self._pixiv_client.get(
                V1_API / "user/related",
                params={
                    "seed_user_id": self._pixiv_client.account.id if id is None else id,
                    "filter": filter,
                    "offset": offset,
                },
            )
        ).json()
        with set_pixiv_client(self._pixiv_client):
            return UserRelatedResult.model_validate(data)
