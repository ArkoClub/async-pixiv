from functools import cached_property
from typing import TYPE_CHECKING

from pydantic import Field

from async_pixiv.model._base import PixivModel
from async_pixiv.typedefs import Datetime, UrlType

if TYPE_CHECKING:
    from async_pixiv.model import ImageUrl, Tag
    from async_pixiv.model.user import User

__all__ = ("Novel", "NovelSeries")


class NovelSeries(PixivModel):
    id: int
    title: str


class Novel(PixivModel):
    id: int
    title: str
    caption: str | None = None
    restrict: int
    x_restrict: int
    is_original: bool
    image_urls: "ImageUrl"
    create_date: Datetime
    tags: list["Tag"]
    page_count: int
    text_length: int
    user: "User"
    series: NovelSeries | None = None
    is_bookmarked: bool
    total_bookmarks: int
    total_view: int
    visible: bool
    is_muted: bool
    is_mypixiv_only: bool
    is_x_restricted: bool
    ai_type: int = Field(alias="novel_ai_type")

    @cached_property
    def link(self) -> UrlType:
        return UrlType(f"https://www.pixiv.net/novel/show.php?id={self.id}")
