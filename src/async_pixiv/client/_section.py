from abc import ABC
from enum import Enum as BaseEnum
from typing import (
    Dict,
    Optional,
    TYPE_CHECKING,
    TypeVar,
    Union,
)

from typing_extensions import Literal
from yarl import URL

from async_pixiv.model.result import (
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
    'USER',
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


class UserIllustType(Enum):
    illust = 'illust'
    manga = 'manga'


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
                Literal['illust', 'manga'], UserIllustType
            ] = UserIllustType.illust,
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


SectionType = TypeVar('SectionType', bound=_Section)
