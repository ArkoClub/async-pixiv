from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, ClassVar, Sequence

from pydantic_core._pydantic_core import ValidationError

from async_pixiv.const import APP_API_HOST
from async_pixiv.error import DataValidationError
from async_pixiv.model import PixivModel
from async_pixiv.model.other.enums import SearchAIType, SearchFilter
from async_pixiv.model.other.result import PageResult
from async_pixiv.typedefs import DurationTypes, ShortTypes

if TYPE_CHECKING:
    from async_pixiv.client import PixivClient

__all__ = ("APIBase",)


# noinspection PyShadowingBuiltins,PyPropertyDefinition
class APIBase[T](ABC):
    _pixiv_client: PixivClient
    _detail_model: ClassVar[type[PixivModel] | None] = None
    _page_result_model: ClassVar[type[PageResult] | None] = None

    @property
    def type(self) -> str:
        return self.__class__.__name__.removesuffix("API").lower()

    def __init__(
        self,
        client: PixivClient,
    ) -> None:
        self._pixiv_client = client

    async def __call__(self, id: int) -> T:
        return await self.detail(id)

    def _get_detail_model(self) -> type[PixivModel]:
        if self._detail_model is None:
            raise RuntimeError(
                f"No detail model registered for {self.__class__.__name__}"
            )
        return self._detail_model

    def _get_page_result_model(self) -> type[PageResult]:
        if self._page_result_model is None:
            raise RuntimeError(
                f"No page result model registered for {self.__class__.__name__}"
            )
        return self._page_result_model

    async def detail(self, id: int) -> T:
        response = await self._pixiv_client.request_get(
            APP_API_HOST / f"v1/{self.type}/detail",
            params={f"{self.type}_id": id, "filter": SearchFilter.ANDROID},
        )
        response.raise_for_result().raise_for_status()

        json_data = response.json()
        obj_type = self._get_detail_model()
        try:
            return obj_type.model_validate(json_data, _pixiv_client=self._pixiv_client)
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

        result_type = self._get_page_result_model()
        return result_type.model_validate(
            response.json(),
            _pixiv_client=self._pixiv_client,
        )

    async def recommended(self) -> PageResult:
        response = await self._pixiv_client.request_get(
            APP_API_HOST / f"v1/{self.type}/recommended"
        )
        response.raise_for_result().raise_for_status()

        result_type = self._get_page_result_model()
        return result_type.model_validate(
            response.json(),
            _pixiv_client=self._pixiv_client,
        )
