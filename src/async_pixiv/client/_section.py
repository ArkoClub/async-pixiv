from abc import ABC
from enum import Enum as BaseEnum
from typing import (
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
    TypeVar,
    Union,
)

from typing_extensions import Literal
from yarl import URL

from async_pixiv.model.result import (
    IllustCommentResult,
    IllustDetailResult,
    IllustRelatedResult,
    IllustSearchResult,
    UserBookmarksIllustsResult,
    UserDetailResult,
    UserIllustsResult,
    UserRelatedResult,
    UserSearchResult,
)

if TYPE_CHECKING:
    from ._client import PixivClient

__all__ = [
    'SearchShort', 'SearchDuration', 'SearchFilter',
    'SectionType',
    'USER', 'ILLUST'
]

API_HOST = URL("https://app-api.pixiv.net")
V1_API = API_HOST / 'v1'
V2_API = API_HOST / 'v2'


class Enum(BaseEnum):
    def __str__(self) -> str:
        # noinspection PyTypeChecker
        return self.value


class SearchShort(Enum):
    date_desc = 'date_desc'
    date_asc = 'date_asc'
    popular_desc = 'popular_desc'
    popular_asc = 'popular_asc'


class SearchDuration(Enum):
    day = 'within_last_day'
    week = 'within_last_week'
    month = 'within_last_month'
    year = 'within_last_year'


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
                'filter': filter, 'offset': offset, **kwargs
            }
        )
        return await request.json()

    async def detail(
            self, id: Optional[int] = None, *, filter: Optional[Union[
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
            self, id: Optional[int] = None, *, filter: Optional[Union[
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
            min_bookmarks: Optional[int] = None,
            max_bookmarks: Optional[int] = None,
            **kwargs
    ) -> IllustSearchResult:
        data = await super(ILLUST, self).search(
            word=word, sort=sort, duration=duration, filter=filter,
            offset=offset, min_bookmarks=min_bookmarks,
            max_bookmarks=max_bookmarks, show_r18='0'
        )
        return IllustSearchResult.parse_obj(data)

    async def detail(
            self, id: Optional[int] = None, *,
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
    ):
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
        breakpoint()
