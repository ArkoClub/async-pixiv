from datetime import date
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Sequence, Union

from typing_extensions import Literal

from async_pixiv.client._section._base import _Section
from async_pixiv.const import V1_API, V2_API
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
from async_pixiv.typedefs import (
    DurationTypes,
    FilterTypes,
    ShortTypes,
    UGOIRA_RESULT_TYPE,
)
from async_pixiv.utils.context import set_pixiv_client
from async_pixiv.utils.enums import SearchFilter, SearchShort

__all__ = ("ILLUST",)


# noinspection PyShadowingBuiltins
class ILLUST(_Section):
    async def follow(self, *, offset: int | None = None) -> IllustSearchResult:
        data = (
            await self._pixiv_client.get(
                V2_API / "illust/follow",
                params={"restrict": "public", "offset": offset},
            )
        ).json()
        with set_pixiv_client(self._pixiv_client):
            return IllustSearchResult.model_validate(data)

    async def search(
        self,
        words: str | Sequence[str],
        *,
        sort: ShortTypes = SearchShort.DateDecrease,
        duration: DurationTypes | None = None,
        target: ShortTypes | None = None,
        filter: FilterTypes | None = SearchFilter.ios,
        offset: int | None = None,
        min_bookmarks: int | None = None,
        max_bookmarks: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        **kwargs,
    ) -> IllustSearchResult:
        if start_date is not None:
            start_date = start_date.strftime("%Y-%m-%d")
        if end_date is not None:
            end_date = end_date.strftime("%Y-%m-%d")
        data = await self._search(
            words=words,
            sort=sort,
            duration=duration,
            filter=filter,
            offset=offset,
            bookmark_num_min=min_bookmarks,
            bookmark_num_max=max_bookmarks,
            target=target,
            start_date=start_date,
            end_date=end_date,
            **kwargs,
        )
        with set_pixiv_client(self._pixiv_client):
            return IllustSearchResult.model_validate(data)

    async def detail(
        self,
        id: int,
        *,
        filter: FilterTypes | None = SearchFilter.ios,
    ) -> IllustDetailResult:
        data = await self._detail(id, filter=filter)
        with set_pixiv_client(self._pixiv_client):
            return IllustDetailResult.model_validate(data)

    async def comments(
        self, id: int, *, offset: int | None = None
    ) -> IllustCommentResult:
        data = (
            await self._pixiv_client.get(
                V1_API / "illust/comments", params={"illust_id": id, "offset": offset}
            )
        ).json()
        with set_pixiv_client(self._pixiv_client):
            return IllustCommentResult.model_validate(data)

    async def related(
        self,
        id: int,
        *,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
        offset: int | None = None,
        seed_ids: Optional[Union[List[int], int]] = None,
    ) -> IllustRelatedResult:
        # noinspection PyTypeChecker
        data = (
            await self._pixiv_client.get(
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
        with set_pixiv_client(self._pixiv_client):
            return IllustRelatedResult.model_validate(data)

    async def recommended(
        self,
        *,
        with_auth: bool = True,
        type: Union[
            Literal["illust", "manga", "novel", "ugoira"], IllustType
        ] = IllustType.illust,
        include_ranking_label: bool = True,
        include_ranking_illusts: Optional[bool] = None,
        offset: int | None = None,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
        max_bookmark_id_for_recommend: int | None = None,
        min_bookmark_id_for_recent_illust: int | None = None,
        bookmark_illust_ids: Optional[Union[List[int], int]] = None,
        include_privacy_policy: Optional[Union[str, List[Union[int, str]]]] = None,
        viewed: Optional[List[int]] = None,
    ) -> RecommendedResult:
        # noinspection SpellCheckingInspection
        data = (
            await self._pixiv_client.get(
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
        with set_pixiv_client(self._pixiv_client):
            return RecommendedResult.model_validate(data)

    async def new_illusts(
        self,
        type: Literal["illust", "manga"] = "illust",
        *,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
        max_illust_id: int | None = None,
    ) -> IllustNewResult:
        data = (
            await self._pixiv_client.get(
                V1_API / "illust/new",
                params={
                    "content_type": type,
                    "max_illust_id": max_illust_id,
                    "filter": filter,
                },
            )
        ).json()
        with set_pixiv_client(self._pixiv_client):
            return IllustNewResult.model_validate(data)

    async def ugoira_metadata(self, id: int) -> UgoiraMetadataResult:
        data = (
            await self._pixiv_client.get(
                V1_API / "ugoira/metadata", params={"illust_id": id}
            )
        ).json()
        with set_pixiv_client(self._pixiv_client):
            return UgoiraMetadataResult.model_validate(data)

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
                await self._pixiv_client.download(
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
                    await self._pixiv_client.download(
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
