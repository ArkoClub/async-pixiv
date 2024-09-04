from abc import ABC, abstractmethod

from pydantic import Field

from async_pixiv.model._base import PixivModel
from async_pixiv.typedefs import URL

__all__ = ("PixivImage", "QualityUrl", "ImageUrl", "AccountImage")


class PixivImage(ABC, PixivModel):
    @property
    @abstractmethod
    def link(self) -> URL:
        pass

    async def download(self, *args, **kwargs):
        return await self.link.download(*args, **kwargs)

class QualityUrl(PixivImage):
    square: URL | None = Field(None, alias="square_medium")
    medium: URL | None = None
    large: URL | None = None
    original: URL | None = None

    @property
    def link(self) -> URL:
        return self.original or self.large or self.medium or self.square

class ImageUrl(QualityUrl):
    pass


class AccountImage(PixivImage):
    small: URL | None = Field(None, alias="px_16x16")
    medium: URL | None = Field(None, alias="px_50x50")
    large: URL | None = Field(None, alias="px_170x170")

    @property
    def link(self) -> URL:
        return self.large or self.medium or self.small
