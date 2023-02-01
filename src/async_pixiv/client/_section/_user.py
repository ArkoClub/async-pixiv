from typing import (
    Optional,
    Union,
)

from typing_extensions import Literal

from async_pixiv.client._section._base import (
    SearchDuration,
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

__all__ = ("USER",)

from async_pixiv.utils.context import set_pixiv_client


# noinspection PyShadowingBuiltins
class USER(_Section):
    async def search(
        self,
        word: str,
        *,
        sort: Union[
            Literal["date_desc", "date_asc", "popular_desc", "popular_asc"], SearchShort
        ] = SearchShort.date_desc,
        duration: Optional[
            Union[
                Literal[
                    "within_last_day",
                    "within_last_week",
                    "within_last_month",
                    "within_last_year",
                ],
                SearchDuration,
            ]
        ] = None,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
        offset: Optional[int] = None,
        **kwargs,
    ) -> UserSearchResult:
        data = await super(USER, self).search(
            word=word,
            sort=sort,
            duration=duration,
            filter=filter,
            offset=offset,
            **kwargs,
        )
        with set_pixiv_client(self._client):
            return UserSearchResult.parse_obj(data)

    async def detail(
        self,
        id: int,
        *,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
    ) -> UserDetailResult:
        if id is None:
            id = self._client.account.id
        data = await super(USER, self).detail(id=id, filter=filter)
        with set_pixiv_client(self._client):
            return UserDetailResult.parse_obj(data)

    async def illusts(
        self,
        id: Optional[int] = None,
        *,
        type: Union[
            Literal["illust", "manga", "novel", "ugoira"], IllustType
        ] = IllustType.illust,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
        offset: Optional[int] = None,
    ) -> UserIllustsResult:
        if id is None:
            id = self._client.account.id
        data = (
            await self._client.get(
                V1_API / "user/illusts",
                params={
                    "user_id": id,
                    "type": type,
                    "filter": filter,
                    "offset": offset,
                },
            )
        ).json()
        with set_pixiv_client(self._client):
            return UserIllustsResult.parse_obj(data)

    async def bookmarks(
        self,
        id: Optional[int] = None,
        *,
        tag: Optional[str] = None,
        max_bookmark_id: Optional[int] = None,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
    ) -> UserBookmarksIllustsResult:
        if id is None:
            id = self._client.account.id
        data = (
            await self._client.get(
                V1_API / "user/bookmarks/illust",
                params={
                    "user_id": id,
                    "filter": filter,
                    "tag": tag,
                    "max_bookmark_id": max_bookmark_id,
                    "restrict": "public",
                },
            )
        ).json()
        with set_pixiv_client(self._client):
            return UserBookmarksIllustsResult.parse_obj(data)

    async def novels(
        self,
        id: Optional[int] = None,
        *,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
        offset: int = None,
    ) -> UserNovelsResult:
        id = self._client.account.id if id is None else id
        data = (
            await self._client.get(
                V1_API / "user/novels",
                params={"user_id": id, "filter": filter, "offset": offset},
            )
        ).json()
        with set_pixiv_client(self._client):
            return UserNovelsResult.parse_obj(data)

    async def related(
        self,
        id: Optional[int] = None,
        *,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
        offset: int = None,
    ) -> UserRelatedResult:
        if id is None:
            id = self._client.account.id
        data = (
            await self._client.get(
                V1_API / "user/related",
                params={"seed_user_id": id, "filter": filter, "offset": offset},
            )
        ).json()
        with set_pixiv_client(self._client):
            return UserRelatedResult.parse_obj(data)
