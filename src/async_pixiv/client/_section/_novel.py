from datetime import date
from typing import Optional, Union

from typing_extensions import Literal

from async_pixiv.client._section._base import _Section
from async_pixiv.const import V1_API, V2_API
from async_pixiv.model.result import (
    NovelContentResult,
    NovelDetailResult,
    NovelSearchResult,
    NovelSeriesResult,
)
from async_pixiv.typedefs import (
    DurationTypes,
    FilterTypes,
    ShortTypes,
)
from async_pixiv.utils.context import set_pixiv_client
from async_pixiv.utils.enums import SearchFilter, SearchShort

__all__ = ("NOVEL",)


# noinspection PyShadowingBuiltins
class NOVEL(_Section):
    async def search(
        self,
        word: str,
        *,
        sort: ShortTypes = SearchShort.DateDecrease,
        duration: DurationTypes | None = None,
        target: ShortTypes | None = None,
        filter: FilterTypes | None = SearchFilter.ios,
        offset: int | None = None,
        min_bookmarks: Optional[int] = None,
        max_bookmarks: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        merge_plain_keyword_results: bool = True,
        include_translated_tag_results: bool = True,
        **kwargs,
    ) -> NovelSearchResult:
        if start_date is not None:
            start_date = start_date.strftime("%Y-%m-%d")
        if end_date is not None:
            end_date = end_date.strftime("%Y-%m-%d")
        data = await super(NOVEL, self).search(
            word,
            sort=sort,
            target=target,
            duration=duration,
            filter=filter,
            offset=offset,
            bookmark_num_min=min_bookmarks,
            bookmark_num_max=max_bookmarks,
            start_date=start_date,
            end_date=end_date,
            merge_plain_keyword_results=merge_plain_keyword_results,
            include_translated_tag_results=include_translated_tag_results,
            **kwargs,
        )
        with set_pixiv_client(self._pixiv_client):
            return NovelSearchResult.parse_obj(data)

    async def detail(
        self,
        id: int,
        *,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
    ) -> NovelDetailResult:
        data = (
            await self._pixiv_client.get(
                V2_API / "novel/detail", params={"novel_id": id}
            )
        ).json()
        with set_pixiv_client(self._pixiv_client):
            return NovelDetailResult.parse_obj(data)

    async def content(self, id: int) -> NovelContentResult:
        data = (
            await self._pixiv_client.get(V1_API / "novel/text", params={"novel_id": id})
        ).json()
        with set_pixiv_client(self._pixiv_client):
            return NovelContentResult.parse_obj(data)

    async def series(
        self,
        id: int,
        *,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
    ) -> NovelSeriesResult:
        data = (
            await self._pixiv_client.get(
                V2_API / "novel/series", params={"series_id": id, "filter": filter}
            )
        ).json()
        with set_pixiv_client(self._pixiv_client):
            return NovelSeriesResult.parse_obj(data)
