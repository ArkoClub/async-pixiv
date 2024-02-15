from enum import IntEnum
from functools import cached_property
from typing import Optional, TYPE_CHECKING

from pydantic import Field
from yarl import URL

from async_pixiv.model._base import PixivModel
from async_pixiv.typedefs import Url

if TYPE_CHECKING:
    from async_pixiv import PixivClient
    from async_pixiv.model.result import NovelSeriesResult

__all__ = [
    "Series",
    "ImageUrl",
    "Tag",
    "TagTranslation",
    "AIType",
    "ProfileImageUrl",
    "ContentRestriction",
]


class Series(PixivModel):
    id: int
    title: str

    @property
    def link(self) -> URL:
        return URL(f"https://www.pixiv.net/novel/series/{self.id}")

    async def detail(
        self, client: Optional["PixivClient"] = None
    ) -> Optional["NovelSeriesResult"]:
        client = client or self._pixiv_client
        return await client.NOVEL.series(self.id)


class ImageUrl(PixivModel):
    square_medium: Optional[Url] = None
    medium: Optional[Url] = None
    large: Optional[Url] = None
    original: Optional[Url] = None

    @property
    def link(self) -> Url:
        return self.original or self.large or self.medium or self.square_medium


class ProfileImageUrl(PixivModel):
    small: Optional[Url] = Field(None, alias="px_16x16")
    medium: Optional[Url] = Field(None, alias="px_50x50")
    large: Optional[Url] = Field(None, alias="px_170x170")

    @cached_property
    def original(self) -> Optional[Url]:
        url = self.small or self.medium or self.large
        return URL(
            "_".join((string_list := url.split("_"))[:-1])
            + "."
            + string_list[-1].split(".")[-1]
        )


class TagTranslation(PixivModel, extra="allow"):
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


class ContentRestriction(IntEnum):
    NO_RESTRICTION = 0
    """用户无限制访问"""

    MILD_RESTRICTION = 1
    """用户有一些限制"""

    STRICT_RESTRICTION = 2
    """用户有严格的限制"""
