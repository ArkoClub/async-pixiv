from enum import IntEnum
from typing import Optional, TYPE_CHECKING

from pydantic import HttpUrl
from yarl import URL

from async_pixiv.model._base import PixivModel, PixivModelConfig

if TYPE_CHECKING:
    from async_pixiv import PixivClient
    from async_pixiv.model.result import NovelSeriesResult

__all__ = ["Series", "ImageUrl", "Tag", "TagTranslation", "AIType"]


class Series(PixivModel):
    id: int
    title: str

    @property
    def link(self) -> URL:
        return URL(f"https://www.pixiv.net/novel/series/{self.id}")

    async def detail(
        self, client: Optional["PixivClient"] = None
    ) -> Optional["NovelSeriesResult"]:
        if client is None:
            from async_pixiv.client import PixivClient

            client = PixivClient.get_client()
        return await client.NOVEL.series(self.id)


class ImageUrl(PixivModel):
    square_medium: Optional[HttpUrl]
    medium: Optional[HttpUrl]
    large: Optional[HttpUrl]
    original: Optional[HttpUrl]

    @property
    def link(self) -> HttpUrl:
        return self.original or self.large or self.medium or self.square_medium


class TagTranslation(PixivModel):
    class Config(PixivModelConfig):
        extra = "allow"

    zh: Optional[str]
    en: Optional[str]
    jp: Optional[str]


class Tag(PixivModel):
    name: str
    translated_name: Optional[str]
    added_by_uploaded_user: Optional[bool]

    def __init__(
        self,
        name: str,
        translated_name: Optional[str] = None,
        added_by_uploaded_user: Optional[bool] = None,
    ) -> None:
        super().__init__(
            name=name,
            translated_name=translated_name,
            added_by_uploaded_user=added_by_uploaded_user,
        )

    def __str__(self) -> str:
        return self.name


class AIType(IntEnum):
    NONE = 0
    """没有使用AI"""

    HALF = 1
    """使用了AI进行辅助"""

    FULL = 2
    """使用AI生成"""
