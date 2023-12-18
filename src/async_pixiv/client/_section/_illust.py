from datetime import date
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Union

from typing_extensions import Literal

from async_pixiv.client._section._base import (
    IllustType,
    SearchDuration,
    SearchFilter,
    SearchShort,
    SearchTarget,
    V1_API,
    V2_API,
    _Section,
)
from async_pixiv.error import ArtWorkTypeError
from async_pixiv.model.illust import IllustType
from async_pixiv.model.result import (
    IllustCommentResult,
    IllustDetailResult,
    IllustNewResult,
    IllustRelatedResult,
    IllustSearchResult,
    RecommendedResult,
    UgoiraMetadataResult,
)
from async_pixiv.utils.context import set_pixiv_client
from async_pixiv.utils.typedefs import UGOIRA_RESULT_TYPE

__all__ = ("ILLUST",)


# noinspection PyShadowingBuiltins
class ILLUST(_Section):
    async def follow(self, *, offset: Optional[int] = None) -> IllustSearchResult:
        data = (
            await self._client.get(
                V2_API / "illust/follow",
                params={"restrict": "public", "offset": offset},
            )
        ).json()
        with set_pixiv_client(self._client):
            return IllustSearchResult.parse_obj(data)

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
        min_bookmarks: Optional[int] = None,
        max_bookmarks: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs,
    ) -> IllustSearchResult:
        if start_date is not None:
            start_date = start_date.strftime("%Y-%m-%d")
        if end_date is not None:
            end_date = end_date.strftime("%Y-%m-%d")
        data = await super(ILLUST, self).search(
            word=word,
            sort=sort,
            duration=duration,
            filter=filter,
            offset=offset,
            bookmark_num_min=min_bookmarks,
            bookmark_num_max=max_bookmarks,
            target=target,
            start_date=start_date,
            end_date=end_date,
        )
        with set_pixiv_client(self._client):
            return IllustSearchResult.parse_obj(data)

    async def detail(
        self,
        id: int,
        *,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
    ) -> IllustDetailResult:
        data = await super(ILLUST, self).detail(id, filter=filter)
        with set_pixiv_client(self._client):
            return IllustDetailResult.parse_obj(data)

    async def comments(
        self, id: int, *, offset: Optional[int] = None
    ) -> IllustCommentResult:
        data = (
            await self._client.get(
                V1_API / "illust/comments", params={"illust_id": id, "offset": offset}
            )
        ).json()
        with set_pixiv_client(self._client):
            return IllustCommentResult.parse_obj(data)

    async def related(
        self,
        id: int,
        *,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
        offset: Optional[int] = None,
        seed_ids: Optional[Union[List[int], int]] = None,
    ) -> IllustRelatedResult:
        # noinspection PyTypeChecker
        data = (
            await self._client.get(
                V2_API / "illust/related",
                params={
                    "illust_id": id,
                    "offset": offset,
                    "filter": filter,
                    "seed_illust_ids": (
                        [seed_ids] if seed_ids is not list else seed_ids
                    ),
                },
            )
        ).json()
        with set_pixiv_client(self._client):
            return IllustRelatedResult.parse_obj(data)

    async def recommended(
        self,
        *,
        with_auth: bool = True,
        type: Union[
            Literal["illust", "manga", "novel", "ugoira"], IllustType
        ] = IllustType.illust,
        include_ranking_label: bool = True,
        include_ranking_illusts: Optional[bool] = None,
        offset: Optional[int] = None,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
        max_bookmark_id_for_recommend: Optional[int] = None,
        min_bookmark_id_for_recent_illust: Optional[int] = None,
        bookmark_illust_ids: Optional[Union[List[int], int]] = None,
        include_privacy_policy: Optional[Union[str, List[Union[int, str]]]] = None,
        viewed: Optional[List[int]] = None,
    ) -> RecommendedResult:
        # noinspection SpellCheckingInspection
        data = (
            await self._client.get(
                V1_API
                / ("illust/recommended" if with_auth else "illust/recommended-nologin"),
                params={
                    "content_type": type,
                    "include_ranking_label": include_ranking_label,
                    "include_ranking_illusts": include_ranking_illusts,
                    "offset": offset,
                    "filter": filter,
                    "viewed": viewed,
                    "max_bookmark_id_for_recommend": max_bookmark_id_for_recommend,
                    "min_bookmark_id_for_recent_illust": min_bookmark_id_for_recent_illust,
                    "bookmark_illust_ids": bookmark_illust_ids,
                    "include_privacy_policy": include_privacy_policy,
                },
            )
        ).json()
        with set_pixiv_client(self._client):
            return RecommendedResult.parse_obj(data)

    async def new_illusts(
        self,
        type: Literal["illust", "manga"] = "illust",
        *,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
        max_illust_id: Optional[int] = None,
    ) -> IllustNewResult:
        data = (
            await self._client.get(
                V1_API / "illust/new",
                params={
                    "content_type": type,
                    "max_illust_id": max_illust_id,
                    "filter": filter,
                },
            )
        ).json()
        with set_pixiv_client(self._client):
            return IllustNewResult.parse_obj(data)

    async def ugoira_metadata(self, id: int) -> UgoiraMetadataResult:
        data = (
            await self._client.get(V1_API / "ugoira/metadata", params={"illust_id": id})
        ).json()
        with set_pixiv_client(self._client):
            return UgoiraMetadataResult.parse_obj(data)

    async def download(
        self,
        id: int,
        *,
        full: bool = False,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
        output: Optional[Union[str, Path, BytesIO]] = None,
    ) -> List[bytes]:
        artwork = (await self.detail(id, filter=filter)).illust
        if artwork.type == IllustType.ugoira:
            raise ArtWorkTypeError(
                "If you want to download a moving image, "
                'please use this method: "download_ugoira"'
            )
        if not full or not artwork.meta_pages:
            return [
                await self._client.download(
                    str(
                        artwork.meta_single_page.original
                        or artwork.image_urls.original
                        or artwork.image_urls.large
                    ),
                    output=output,
                )
            ]
        else:
            result: List[bytes] = []
            for meta_page in artwork.meta_pages:
                result.append(
                    await self._client.download(
                        str(
                            meta_page.image_urls.original or meta_page.image_urls.large
                        ),
                        output=output,
                    )
                )
            return result

    async def download_ugoira(
        self, id: int, *, type: UGOIRA_RESULT_TYPE = "zip"
    ) -> Union[bytes, List[bytes], None]:
        return await (await self.detail(id)).illust.download_ugoira(type=type)
