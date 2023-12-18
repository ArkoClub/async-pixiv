from abc import ABC
from typing import (
    Dict,
    Optional,
    TYPE_CHECKING,
    TypeVar,
    Union,
)

from typing_extensions import Literal
from yarl import URL

from async_pixiv.utils.enums import (
    Enum,
    SearchDuration,
    SearchFilter,
    SearchShort,
    SearchTarget,
)

if TYPE_CHECKING:
    from async_pixiv.client._client import PixivClient

API_HOST = URL("https://app-api.pixiv.net")
AJAX_HOST = URL("https://www.pixiv.net/ajax")
V1_API = API_HOST / "v1"
V2_API = API_HOST / "v2"


# noinspection PyShadowingBuiltins
class _Section(ABC):
    _client: "PixivClient"
    _type: str

    @property
    def type(self) -> str:
        return self._type

    def __init_subclass__(cls, **kwargs) -> None:
        cls._type = cls.__name__.lower()

    def __init__(self, client: "PixivClient") -> None:
        self._client = client

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
        ] = None,
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
    ) -> Dict:
        # noinspection PyTypeChecker
        response = await self._client.get(
            V1_API / f"search/{self._type}",
            params={
                "word": word,
                "sort": sort,
                "duration": duration,
                "filter": filter,
                "offset": offset,
                "search_target": target,
                **kwargs,
            },
        )
        return response.json()

    async def detail(
        self,
        id: int,
        *,
        filter: Optional[
            Union[Literal["for_android", "for_ios"], SearchFilter]
        ] = SearchFilter.ios,
    ) -> Dict:
        request = await self._client.get(
            V1_API / f"{self._type}/detail",
            params={f"{self._type}_id": id, "filter": filter},
        )
        return request.json()


SectionType = TypeVar("SectionType", bound=_Section)


class IllustType(Enum):
    illust = "illust"
    manga = "manga"
    ugoira = "ugoira"
    novel = "novel"
