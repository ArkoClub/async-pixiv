from abc import ABC
from typing import AsyncIterator, Iterator, Self

from pydantic import Field

from async_pixiv.model._base import PixivModel
from async_pixiv.model.other.image import QualityUrl
from async_pixiv.typedefs import UrlType
from async_pixiv.utils.context import set_pixiv_client


class PageResult[T](ABC, PixivModel):
    previews: list[T] = []
    next_url: UrlType | None = None

    def __iter__(self) -> Iterator[T]:
        return iter(self.previews)

    async def next(self) -> Self | None:
        if self.next_url is not None:
            with set_pixiv_client(self._pixiv_client) as client:
                response = await client.request_get(self.next_url)
                return self.__class__.model_validate(response.raise_error().json())
        return None

    async def iter_all_pages(self) -> AsyncIterator[T]:
        for result in self:
            yield result
        next_results = await self.next()
        while next_results is not None:
            for result in next_results:
                yield result
            next_results = await next_results.next()


class UgoiraFrameMetadata(PixivModel):
    file: str
    delay: int


class UgoiraMetadata(PixivModel):
    zip_url: QualityUrl = Field(alias="zip_urls")
    frames: list[UgoiraFrameMetadata]


class UgoiraMetadataResult(PixivModel):
    metadata: UgoiraMetadata = Field(alias="ugoira_metadata")
