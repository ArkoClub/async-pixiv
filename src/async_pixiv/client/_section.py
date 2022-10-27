from abc import ABC
from datetime import date
from enum import Enum as BaseEnum
from io import BytesIO
from pathlib import Path
from typing import (
    Dict,
    Iterator,
    List,
    Optional,
    TYPE_CHECKING,
    TypeVar,
    Union,
)
from zipfile import ZipFile

from typing_extensions import Literal
from yarl import URL

from async_pixiv.model.result import (
    IllustCommentResult,
    IllustDetailResult,
    IllustNewResult,
    IllustRelatedResult,
    IllustSearchResult,
    NovelContentResult,
    NovelDetailResult,
    NovelSearchResult,
    NovelSeriesResult,
    RecommendedResult,
    UgoiraMetadataResult,
    UserBookmarksIllustsResult,
    UserDetailResult,
    UserIllustsResult,
    UserNovelsResult,
    UserRelatedResult,
    UserSearchResult,
)
from ..error import ArtWorkTypeError
from ..model.artwork import ArtWorkType

if TYPE_CHECKING:
    from ._client import PixivClient

__all__ = [
    'SearchTarget', 'SearchShort', 'SearchDuration', 'SearchFilter',
    'SectionType',
    'USER', 'ILLUST', 'NOVEL'
]

API_HOST = URL("https://app-api.pixiv.net")
V1_API = API_HOST / 'v1'
V2_API = API_HOST / 'v2'


class Enum(BaseEnum):
    def __str__(self) -> str:
        # noinspection PyTypeChecker
        return self.value


class SearchTarget(Enum):
    partial = 'partial_match_for_tags'  # 标签部分一致
    full = 'exact_match_for_tags'  # 标签完全一致
    text = 'text'  # 正文
    keyword = 'keyword'  # 关键词


class SearchShort(Enum):
    date_desc = 'date_desc'
    date_asc = 'date_asc'
    popular_desc = 'popular_desc'
    popular_asc = 'popular_asc'


class SearchDuration(Enum):
    day = 'within_last_day'
    week = 'within_last_week'
    month = 'within_last_month'


class SearchFilter(Enum):
    android = 'for_android'
    ios = 'for_ios'


# noinspection PyShadowingBuiltins
class _Section(ABC):
    _client: "PixivClient"
    _type: str = ''

    @property
    def type(self) -> str:
        return self._type

    def __init__(self, client: "PixivClient") -> None:
        self._client = client

    async def search(
            self,
            word: str, *,
            sort: Union[
                Literal['date_desc', 'date_asc', 'popular_desc', 'popular_asc'],
                SearchShort
            ] = SearchShort.date_desc,
            target: Union[
                SearchTarget,
                Literal[
                    'partial_match_for_tags', 'keyword',
                    'exact_match_for_tags', 'text'
                ]
            ] = None,
            duration: Optional[Union[
                Literal[
                    'within_last_day',
                    'within_last_week',
                    'within_last_month',
                    'within_last_year'
                ], SearchDuration
            ]] = None,
            filter: Optional[Union[
                Literal['for_android', 'for_ios'], SearchFilter
            ]] = SearchFilter.ios,
            offset: Optional[int] = None, **kwargs
    ) -> Dict:
        request = await self._client.get(
            V1_API / f'search/{self._type}',
            params={
                'word': word, 'sort': sort, 'duration': duration,
                'filter': filter, 'offset': offset, 'search_target': target,
                **kwargs
            }
        )
        return await request.json()

    async def detail(
            self, id: int, *, filter: Optional[Union[
                Literal['for_android', 'for_ios'], SearchFilter
            ]] = SearchFilter.ios
    ) -> Dict:
        request = await self._client.get(
            V1_API / f'{self._type}/detail',
            params={f'{self._type}_id': id, 'filter': filter}
        )
        return await request.json()


SectionType = TypeVar('SectionType', bound=_Section)


class IllustType(Enum):
    illust = 'illust'
    manga = 'manga'
    ugoira = 'ugoira'
    novel = 'novel'


# noinspection PyShadowingBuiltins
class USER(_Section):
    _type = 'user'

    async def search(
            self,
            word: str, *,
            sort: Union[
                Literal['date_desc', 'date_asc', 'popular_desc', 'popular_asc'],
                SearchShort
            ] = SearchShort.date_desc,
            duration: Optional[Union[
                Literal[
                    'within_last_day',
                    'within_last_week',
                    'within_last_month',
                    'within_last_year'
                ], SearchDuration
            ]] = None,
            filter: Optional[Union[
                Literal['for_android', 'for_ios'], SearchFilter
            ]] = SearchFilter.ios,
            offset: Optional[int] = None, **kwargs
    ) -> UserSearchResult:
        data = await super(USER, self).search(
            word=word, sort=sort, duration=duration, filter=filter,
            offset=offset, **kwargs
        )
        return UserSearchResult.parse_obj(data)

    async def detail(
            self, id: int, *, filter: Optional[Union[
                Literal['for_android', 'for_ios'], SearchFilter
            ]] = SearchFilter.ios
    ) -> UserDetailResult:
        if id is None:
            id = self._client.account.id
        data = await super(USER, self).detail(id=id, filter=filter)
        return UserDetailResult.parse_obj(data)

    async def illusts(
            self, id: Optional[int] = None, *,
            type: Union[
                Literal['illust', 'manga', 'novel', 'ugoira'], IllustType
            ] = IllustType.illust,
            filter: Optional[Union[
                Literal['for_android', 'for_ios'], SearchFilter
            ]] = SearchFilter.ios,
            offset: Optional[int] = None
    ) -> UserIllustsResult:
        if id is None:
            id = self._client.account.id
        data = await (await self._client.get(
            V1_API / "user/illusts",
            params={
                'user_id': id, 'type': type, 'filter': filter, 'offset': offset
            }
        )).json()
        return UserIllustsResult.parse_obj(data)

    async def bookmarks(
            self, id: Optional[int] = None, *,
            tag: Optional[str] = None,
            max_bookmark_id: Optional[int] = None,
            filter: Optional[Union[
                Literal['for_android', 'for_ios'], SearchFilter
            ]] = SearchFilter.ios,
    ) -> UserBookmarksIllustsResult:
        if id is None:
            id = self._client.account.id
        data = await (await self._client.get(
            V1_API / "user/bookmarks/illust",
            params={
                'user_id': id, 'filter': filter, 'tag': tag,
                'max_bookmark_id': max_bookmark_id, 'restrict': 'public'
            }
        )).json()
        return UserBookmarksIllustsResult.parse_obj(data)

    async def novels(
            self, id: Optional[int] = None, *,
            filter: Optional[Union[
                Literal['for_android', 'for_ios'], SearchFilter
            ]] = SearchFilter.ios,
            offset: int = None
    ) -> UserNovelsResult:
        id = self._client.account.id if id is None else id
        data = await (await self._client.get(
            V1_API / "user/novels",
            params={'user_id': id, 'filter': filter, 'offset': offset}
        )).json()
        return UserNovelsResult.parse_obj(data)

    async def related(
            self, id: Optional[int] = None, *,
            filter: Optional[Union[
                Literal['for_android', 'for_ios'], SearchFilter
            ]] = SearchFilter.ios,
            offset: int = None,
    ) -> UserRelatedResult:
        if id is None:
            id = self._client.account.id
        data = await (await self._client.get(
            V1_API / "user/related",
            params={
                'seed_user_id': id, 'filter': filter, 'offset': offset
            }
        )).json()
        return UserRelatedResult.parse_obj(data)


# noinspection PyShadowingBuiltins
class ILLUST(_Section):
    _type = 'illust'

    async def follow(
            self, *, offset: Optional[int] = None
    ) -> IllustSearchResult:
        data = await (await self._client.get(
            V2_API / "illust/follow",
            params={'restrict': 'public', 'offset': offset}
        )).json()
        return IllustSearchResult.parse_obj(data)

    async def search(
            self,
            word: str, *,
            sort: Union[
                Literal['date_desc', 'date_asc', 'popular_desc', 'popular_asc'],
                SearchShort
            ] = SearchShort.date_desc,
            target: Union[
                SearchTarget,
                Literal[
                    'partial_match_for_tags', 'keyword',
                    'exact_match_for_tags', 'text'
                ]
            ] = SearchTarget.partial,
            duration: Optional[Union[
                Literal[
                    'within_last_day',
                    'within_last_week',
                    'within_last_month',
                ], SearchDuration
            ]] = None,
            filter: Optional[Union[
                Literal['for_android', 'for_ios'], SearchFilter
            ]] = SearchFilter.ios,
            offset: Optional[int] = None,
            min_bookmarks: Optional[int] = None,
            max_bookmarks: Optional[int] = None,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None,
            **kwargs
    ) -> IllustSearchResult:
        if start_date is not None:
            start_date = start_date.strftime('%Y-%m-%d')
        if end_date is not None:
            end_date = end_date.strftime('%Y-%m-%d')
        data = await super(ILLUST, self).search(
            word=word, sort=sort, duration=duration, filter=filter,
            offset=offset, bookmark_num_min=min_bookmarks,
            bookmark_num_max=max_bookmarks, target=target,
            start_date=start_date, end_date=end_date,
        )
        return IllustSearchResult.parse_obj(data)

    async def detail(
            self, id: int, *,
            filter: Optional[Union[
                Literal['for_android', 'for_ios'], SearchFilter
            ]] = SearchFilter.ios
    ) -> IllustDetailResult:
        data = await super(ILLUST, self).detail(id, filter=filter)
        return IllustDetailResult.parse_obj(data)

    async def comments(
            self, id: int, *, offset: Optional[int] = None
    ) -> IllustCommentResult:
        data = await (await self._client.get(
            V1_API / "illust/comments", params={
                'illust_id': id, "offset": offset
            }
        )).json()
        return IllustCommentResult.parse_obj(data)

    async def related(
            self, id: int, *,
            filter: Optional[Union[
                Literal['for_android', 'for_ios'], SearchFilter
            ]] = SearchFilter.ios,
            offset: Optional[int] = None,
            seed_ids: Optional[Union[List[int], int]] = None
    ) -> IllustRelatedResult:
        data = await (await self._client.get(
            V2_API / "illust/related", params={
                'illust_id': id, "offset": offset, 'filter': filter,
                'seed_illust_ids': (
                    [seed_ids] if seed_ids is not list else seed_ids
                )
            }
        )).json()
        return IllustRelatedResult.parse_obj(data)

    async def recommended(
            self, *, with_auth: bool = True, type: Union[
                Literal['illust', 'manga', 'novel', 'ugoira'], IllustType
            ] = IllustType.illust,
            include_ranking_label: bool = True,
            include_ranking_illusts: Optional[bool] = None,
            offset: Optional[int] = None,
            filter: Optional[Union[
                Literal['for_android', 'for_ios'], SearchFilter
            ]] = SearchFilter.ios,
            max_bookmark_id_for_recommend: Optional[int] = None,
            min_bookmark_id_for_recent_illust: Optional[int] = None,
            bookmark_illust_ids: Optional[Union[List[int], int]] = None,
            include_privacy_policy: Optional[Union[
                str, List[Union[int, str]]
            ]] = None,
            viewed: Optional[List[int]] = None
    ) -> RecommendedResult:
        data = await (await self._client.get(
            V1_API / (
                "illust/recommended"
                if with_auth else
                "illust/recommended-nologin"
            ), params={
                'content_type': type,
                'include_ranking_label': include_ranking_label,
                'include_ranking_illusts': include_ranking_illusts,
                'offset': offset, 'filter': filter, 'viewed': viewed,
                'max_bookmark_id_for_recommend': max_bookmark_id_for_recommend,
                'min_bookmark_id_for_recent_illust':
                    min_bookmark_id_for_recent_illust,
                'bookmark_illust_ids': bookmark_illust_ids,
                'include_privacy_policy': include_privacy_policy,
            }
        )).json()
        return RecommendedResult.parse_obj(data)

    async def new_illusts(
            self, type: Literal['illust', 'manga'] = 'illust', *,
            filter: Optional[Union[
                Literal['for_android', 'for_ios'], SearchFilter
            ]] = SearchFilter.ios,
            max_illust_id: Optional[int] = None
    ) -> IllustNewResult:
        data = await (await self._client.get(
            V1_API / 'illust/new',
            params={
                'content_type': type,
                'max_illust_id': max_illust_id,
                'filter': filter,
            }
        )).json()
        return IllustNewResult.parse_obj(data)

    async def ugoira_metadata(self, id: int) -> UgoiraMetadataResult:
        data = await (await self._client.get(
            V1_API / 'ugoira/metadata', params={'illust_id': id}
        )).json()
        return UgoiraMetadataResult.parse_obj(data)

    async def download(
            self, id: int, *,
            full: bool = False,
            filter: Optional[Union[
                Literal['for_android', 'for_ios'], SearchFilter
            ]] = SearchFilter.ios,
            output: Optional[Union[str, Path, BytesIO]] = None
    ) -> List[bytes]:
        artwork = (await self.detail(id, filter=filter)).illust
        if artwork.type == ArtWorkType.ugoira:
            raise ArtWorkTypeError(
                'If you want to download a moving image, '
                'please use this method: \"download_ugoira\"'
            )
        if not full or not artwork.meta_pages:
            return [await self._client.download(
                str(
                    artwork.meta_single_page.original or
                    artwork.image_urls.original or
                    artwork.image_urls.large
                ), output=output
            )]
        else:
            result: List[bytes] = []
            for meta_page in artwork.meta_pages:
                result.append(
                    await self._client.download(
                        str(
                            meta_page.image_urls.original or
                            meta_page.image_urls.large
                        ), output=output
                    )
                )
            return result

    async def download_ugoira(
            self, id: int, *,
            type: Literal['zip', 'jpg', 'all', 'iter'] = 'zip',
    ) -> Optional[Union[
        ZipFile, List[bytes], Dict[str, Union[ZipFile, List[bytes]]],
        Iterator[bytes]
    ]]:
        metadata = (await self.ugoira_metadata(id)).metadata
        zip_url = metadata.zip_url
        data = await self._client.download(
            zip_url.original or zip_url.large or zip_url.medium,
        )
        if data is None:
            return None
        zip_file = ZipFile(BytesIO(data))
        if type == 'zip':
            return zip_file
        frames = []
        for frame_info in metadata.frames:
            with zip_file.open(frame_info.file) as f:
                frames.append(f.read())
        if type == 'jpg':
            return frames
        elif type == 'iter':
            return iter(frames)
        else:
            return {'zip': zip_file, 'frames': frames}


# noinspection PyShadowingBuiltins
class NOVEL(_Section):
    _type = "novel"

    async def search(
            self,
            word: str, *,
            sort: Union[
                Literal['date_desc', 'date_asc', 'popular_desc', 'popular_asc'],
                SearchShort
            ] = SearchShort.date_desc,
            target: Union[
                SearchTarget,
                Literal[
                    'partial_match_for_tags', 'keyword',
                    'exact_match_for_tags', 'text'
                ]
            ] = SearchTarget.partial,
            duration: Optional[Union[
                Literal[
                    'within_last_day',
                    'within_last_week',
                    'within_last_month',
                    'within_last_year'
                ], SearchDuration
            ]] = None,
            filter: Optional[Union[
                Literal['for_android', 'for_ios'], SearchFilter
            ]] = SearchFilter.ios,
            offset: Optional[int] = None,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None,
            merge_plain_keyword_results: bool = True,
            include_translated_tag_results: bool = True, **kwargs
    ) -> NovelSearchResult:
        if start_date is not None:
            start_date = start_date.strftime('%Y-%m-%d')
        if end_date is not None:
            end_date = end_date.strftime('%Y-%m-%d')
        data = await super(NOVEL, self).search(
            word, sort=sort, target=target, duration=duration, filter=filter,
            offset=offset, start_date=start_date, end_date=end_date,
            merge_plain_keyword_results=merge_plain_keyword_results,
            include_translated_tag_results=include_translated_tag_results
        )
        return NovelSearchResult.parse_obj(data)

    async def detail(
            self, id: int, *, filter: Optional[Union[
                Literal['for_android', 'for_ios'], SearchFilter
            ]] = SearchFilter.ios
    ) -> NovelDetailResult:
        data = await (await self._client.get(
            V2_API / 'novel/detail', params={'novel_id': id}
        )).json()
        return NovelDetailResult.parse_obj(data)

    async def content(self, id: int) -> NovelContentResult:
        data = await (await self._client.get(
            V1_API / 'novel/text', params={'novel_id': id}
        )).json()
        return NovelContentResult.parse_obj(data)

    async def series(
            self, id: int, *, filter: Optional[Union[
                Literal['for_android', 'for_ios'], SearchFilter
            ]] = SearchFilter.ios
    ) -> NovelSeriesResult:
        data = await (await self._client.get(
            V2_API / 'novel/series', params={'series_id': id, 'filter': filter}
        )).json()
        return NovelSeriesResult.parse_obj(data)
