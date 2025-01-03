from __future__ import annotations

from abc import ABC
from importlib import import_module
from threading import RLock as Lock
from typing import TYPE_CHECKING, Optional, Sequence

from pydantic_core._pydantic_core import ValidationError

from async_pixiv.const import APP_API_HOST
from async_pixiv.error import ClientNotFindError, DataValidationError
from async_pixiv.model import PixivModel
from async_pixiv.model.other.enums import SearchFilter
from async_pixiv.model.other.result import PageResult
from async_pixiv.typedefs import DurationTypes, ShortTypes
from async_pixiv.utils.context import get_pixiv_client, set_pixiv_client

if TYPE_CHECKING:
    from async_pixiv.client import PixivClient

__all__ = ("APIBase",)

_TYPE_CATCH_DICT: dict[str, type[PageResult | PixivModel]] = {}


# noinspection PyShadowingBuiltins,PyPropertyDefinition
class APIBase[T](ABC):
    _lock: Lock = Lock()

    _pixiv_client: "PixivClient"
    _type: str

    @property
    def type(self) -> str:
        return self._type

    def __init_subclass__(cls, **kwargs) -> None:
        cls._type = cls.__name__.removesuffix("API").lower()

    def __init__(
        self,
        client: Optional["PixivClient"] = None,
    ) -> None:
        client = client or get_pixiv_client()
        if client is None:
            raise ClientNotFindError()
        self._pixiv_client = client

    async def __call__(self, id: int) -> T:
        return await self.detail(id)

    async def detail(self, id: int) -> T:
        response = await self._pixiv_client.request_get(
            APP_API_HOST / f"v1/{self._type}/detail",
            params={f"{self._type}_id": id, "filter": SearchFilter.ANDROID},
        )
        response.raise_for_result().raise_for_status()

        json_data = response.json()
        obj_type_name = self.type.title() + "Detail"

        with self._lock:
            if obj_type_name not in _TYPE_CATCH_DICT:
                _TYPE_CATCH_DICT[obj_type_name] = import_module(
                    f"async_pixiv.client.api._{self._type}"
                ).__getattribute__(obj_type_name)

        obj_type = _TYPE_CATCH_DICT[obj_type_name]
        with set_pixiv_client(self._pixiv_client):
            try:
                return obj_type.model_validate(json_data)
            except ValidationError:
                raise DataValidationError(json_data)

    async def search(
        self,
        words: str | Sequence[str],
        *,
        sort: ShortTypes | None = None,
        duration: DurationTypes | None = None,
        offset: int | None = None,
        **kwargs,
    ) -> PageResult:
        response = await self._pixiv_client.request_get(
            APP_API_HOST / f"v1/search/{self.type}",
            params={
                "word": words if isinstance(words, str) else " ".join(words),
                "sort": sort,
                "duration": duration,
                "offset": offset,
                **kwargs,
            },
        )
        response.raise_error()

        search_result_type_name = f"{self.type.title()}PageResult"

        with self._lock:
            if search_result_type_name not in _TYPE_CATCH_DICT:
                _TYPE_CATCH_DICT[search_result_type_name] = import_module(
                    f"async_pixiv.client.api._{self._type}"
                ).__getattribute__(search_result_type_name)

        search_result_type = _TYPE_CATCH_DICT[search_result_type_name]
        with set_pixiv_client(self._pixiv_client):
            return search_result_type.model_validate(response.json())

    async def recommended(self) -> PageResult:
        response = await self._pixiv_client.request_get(
            APP_API_HOST / f"v1/{self.type}/recommended"
        )
        response.raise_for_result().raise_for_status()

        search_result_type_name = f"{self.type.title()}PageResult"

        with self._lock:
            if search_result_type_name not in _TYPE_CATCH_DICT:
                _TYPE_CATCH_DICT[search_result_type_name] = import_module(
                    f"async_pixiv.client.api._{self._type}"
                ).__getattribute__(search_result_type_name)

        search_result_type = _TYPE_CATCH_DICT[search_result_type_name]
        with set_pixiv_client(self._pixiv_client):
            return search_result_type.model_validate(response.json())
