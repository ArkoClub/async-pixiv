from __future__ import annotations

from abc import ABC
from importlib import import_module
from typing import TYPE_CHECKING, Sequence

from pydantic_core._pydantic_core import ValidationError

from async_pixiv.const import APP_API_HOST
from async_pixiv.error import ClientNotFindError, DataValidationError
from async_pixiv.model import PixivModel
from async_pixiv.model.other.enums import SearchAIType, SearchFilter
from async_pixiv.model.other.result import PageResult
from async_pixiv.typedefs import DurationTypes, ShortTypes
from async_pixiv.utils.context import get_pixiv_client, set_pixiv_client

if TYPE_CHECKING:
    from async_pixiv.client import PixivClient

__all__ = ("APIBase",)

_TYPE_CACHE: dict[str, type[PageResult | PixivModel]] = {}


# noinspection PyShadowingBuiltins,PyPropertyDefinition
class APIBase[T](ABC):
    _pixiv_client: PixivClient
    _type: str

    @property
    def type(self) -> str:
        return self._type

    def __init_subclass__(cls, **kwargs) -> None:
        cls._type = cls.__name__.removesuffix("API").lower()

    def __init__(
        self,
        client: PixivClient | None = None,
    ) -> None:
        client = client or get_pixiv_client()
        if client is None:
            raise ClientNotFindError()
        self._pixiv_client = client

    async def __call__(self, id: int) -> T:
        return await self.detail(id)

    def _resolve_type(self, type_name: str) -> type[PageResult | PixivModel]:
        if type_name not in _TYPE_CACHE:
            _TYPE_CACHE[type_name] = getattr(
                import_module(f"async_pixiv.client.api._{self._type}"),
                type_name,
            )
        return _TYPE_CACHE[type_name]

    async def detail(self, id: int) -> T:
        response = await self._pixiv_client.request_get(
            APP_API_HOST / f"v1/{self._type}/detail",
            params={f"{self._type}_id": id, "filter": SearchFilter.ANDROID},
        )
        response.raise_for_result().raise_for_status()

        json_data = response.json()
        obj_type = self._resolve_type(f"{self.type.title()}Detail")
        with set_pixiv_client(self._pixiv_client):
            try:
                return obj_type.model_validate(json_data)
            except ValidationError as exc:
                raise DataValidationError(json_data) from exc

    async def search(
        self,
        words: str | Sequence[str],
        *,
        sort: ShortTypes | None = None,
        duration: DurationTypes | None = None,
        offset: int | None = None,
        search_ai_type: SearchAIType | None = None,
        **kwargs,
    ) -> PageResult:
        response = await self._pixiv_client.request_get(
            APP_API_HOST / f"v1/search/{self.type}",
            params={
                "word": words if isinstance(words, str) else " ".join(words),
                "sort": sort,
                "duration": duration,
                "offset": offset,
                "search_ai_type": search_ai_type,
                **kwargs,
            },
        )
        response.raise_error()

        result_type = self._resolve_type(f"{self.type.title()}PageResult")
        with set_pixiv_client(self._pixiv_client):
            return result_type.model_validate(response.json())

    async def recommended(self) -> PageResult:
        response = await self._pixiv_client.request_get(
            APP_API_HOST / f"v1/{self.type}/recommended"
        )
        response.raise_for_result().raise_for_status()

        result_type = self._resolve_type(f"{self.type.title()}PageResult")
        with set_pixiv_client(self._pixiv_client):
            return result_type.model_validate(response.json())
