from abc import ABC
from typing import Dict, Sequence, TYPE_CHECKING, TypeVar

from async_pixiv.const import V1_API
from async_pixiv.typedefs import DurationTypes, FilterTypes, ShortTypes
from async_pixiv.utils.enums import (
    SearchFilter,
    SearchShort,
)

if TYPE_CHECKING:
    from async_pixiv.client._client import PixivClient

__all__ = ("_Section", "SectionType")


# noinspection PyShadowingBuiltins
class _Section(ABC):
    _pixiv_client: "PixivClient"
    _type: str

    @property
    def type(self) -> str:
        return self._type

    @property
    def client(self) -> "PixivClient":
        return self._pixiv_client

    def __init_subclass__(cls, **kwargs) -> None:
        cls._type = cls.__name__.lower()

    def __init__(self, client: "PixivClient") -> None:
        self._pixiv_client = client

    async def _search(
        self,
        words: str | Sequence[str],
        *,
        sort: ShortTypes = SearchShort.DateDecrease,
        duration: DurationTypes | None = None,
        target: ShortTypes | None = None,
        filter: FilterTypes | None = SearchFilter.ios,
        offset: int | None = None,
        **kwargs,
    ) -> Dict:
        # noinspection PyTypeChecker
        response = await self._pixiv_client.get(
            V1_API / f"search/{self._type}",
            params={
                "word": words if isinstance(words, str) else " ".join(words),
                "sort": sort,
                "duration": duration,
                "filter": filter,
                "offset": offset,
                "search_target": target,
                **kwargs,
            },
        )
        return response.json()

    async def _detail(
        self,
        id: int,
        *,
        filter: FilterTypes | None = None,
    ) -> Dict:
        request = await self._pixiv_client.get(
            V1_API / f"{self._type}/detail",
            params={f"{self._type}_id": id, "filter": filter or SearchFilter.ios},
        )
        return request.json()


SectionType = TypeVar("SectionType", bound=_Section)
