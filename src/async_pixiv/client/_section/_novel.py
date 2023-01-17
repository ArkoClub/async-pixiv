from datetime import date
from typing import (
    Optional,
    Union,
)

from typing_extensions import Literal

from async_pixiv.client._section._base import (
    SearchDuration,
    SearchFilter,
    SearchShort,
    SearchTarget,
    V1_API,
    V2_API,
    _Section,
)
from async_pixiv.model.result import (
    NovelContentResult,
    NovelDetailResult,
    NovelSearchResult,
    NovelSeriesResult,
)


# noinspection PyShadowingBuiltins
class NOVEL(_Section):
    async def search(
        self,
        word: str,
        *,
        sort: Union[
            Literal["date_desc", "date_asc", "popular_desc", "popular_asc"], SearchShort
        ] = SearchShort.date_desc,
        target: Union[
            SearchTarget,
            Literal[
                "partial_match_for_tags", "keyword", "exact_match_for_tags", "text"
            ],
        ] = SearchTarget.partial,
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
            start_date=start_date,
            end_date=end_date,
            merge_plain_keyword_results=merge_plain_keyword_results,
            include_translated_tag_results=include_translated_tag_results,
        )
        return NovelSearchResult.parse_obj(data)

    async def detail(
        self,
        id: int,
        *,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
    ) -> NovelDetailResult:
        data = await (
            await self._client.get(V2_API / "novel/detail", params={"novel_id": id})
        ).json()
        return NovelDetailResult.parse_obj(data)

    async def content(self, id: int) -> NovelContentResult:
        data = await (
            await self._client.get(V1_API / "novel/text", params={"novel_id": id})
        ).json()
        return NovelContentResult.parse_obj(data)

    async def series(
        self,
        id: int,
        *,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
    ) -> NovelSeriesResult:
        data = await (
            await self._client.get(
                V2_API / "novel/series", params={"series_id": id, "filter": filter}
            )
        ).json()
        return NovelSeriesResult.parse_obj(data)
