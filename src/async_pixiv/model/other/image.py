from abc import ABC, abstractmethod

from pydantic import Field

from async_pixiv.model._base import PixivModel
from async_pixiv.typedefs import UrlType

__all__ = ("PixivImage", "QualityUrl", "ImageUrl", "AccountImage")


class PixivImage(ABC, PixivModel):
    @property
    @abstractmethod
    def link(self) -> UrlType:
        pass

    async def download(self, *args, **kwargs):
        return await self.link.download(*args, **kwargs)


class QualityUrl(PixivImage):
    square: UrlType | None = Field(None, alias="square_medium")
    medium: UrlType | None = None
    large: UrlType | None = None
    original: UrlType | None = None

    @property
    def link(self) -> UrlType:
        return self.original or self.large or self.medium or self.square


class ImageUrl(QualityUrl):
    pass


class AccountImage(PixivImage):
    small: UrlType | None = Field(None, alias="px_16x16")
    medium: UrlType | None = Field(None, alias="px_50x50")
    large: UrlType | None = Field(None, alias="px_170x170")

    @property
    def link(self) -> UrlType:
        return self.large or self.medium or self.small
