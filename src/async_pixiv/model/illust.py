from functools import cached_property
from typing import Any

from pydantic import Field

from async_pixiv.model._base import PixivModel
from async_pixiv.model.other.image import ImageUrl
from async_pixiv.model.other.tag import Tag
from async_pixiv.model.user import User
from async_pixiv.typedefs import Datetime, Enum, URL


class IllustType(Enum):
    illust = "illust"
    ugoira = "ugoira"
    manga = "manga"
    novel = "novel"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, IllustType):
            return self.value == other.value
        else:
            try:
                return self.value == str(other)
            except (TypeError, ValueError):
                return False


class IllustMetaSinglePage(PixivModel):
    original: URL | None = Field(None, alias="original_image_url")

    @property
    def link(self) -> URL | None:
        return self.original


class IllustMetaPage(PixivModel):
    image_urls: ImageUrl


class Illust(PixivModel):
    id: int
    title: str
    type: "IllustType"
    image_urls: ImageUrl
    caption: str | None = None
    restrict: int
    user: User
    tags: list[Tag] = []
    tools: list[str]
    create_date: Datetime
    page_count: int
    width: int
    height: int
    sanity_level: int
    x_restrict: int
    meta_single_page: IllustMetaSinglePage | None = None
    meta_pages: list[IllustMetaPage]
    total_view: int
    total_bookmarks: int
    is_bookmarked: bool
    visible: bool
    is_muted: bool
    ai_type: int = Field(alias="illust_ai_type")
    illust_book_style: int

    comment_access_control: int | None = None
    total_comments: int | None = None

    @cached_property
    def link(self) -> URL:
        return URL(f"https://www.pixiv.net/artworks/{self.id}")
