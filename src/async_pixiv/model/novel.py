import datetime
from functools import cached_property

from pydantic import Field

from async_pixiv.model._base import PixivModel
from async_pixiv.model.other.image import ImageUrl, PixivImage
from async_pixiv.model.other.tag import Tag
from async_pixiv.model.user import User
from async_pixiv.typedefs import Datetime, UrlType

__all__ = (
    "Novel",
    "NovelSeries",
    "NovelRating",
    "NovelText",
    "NovelSeriesNavigationNovel",
    "NovelSeriesNavigation",
    "NovelGlossaryItem",
    "NovelImageUrl",
    "NovelImage",
    "NovelIllustUser",
    "NovelIllust",
)


class NovelSeriesNavigationNovel(PixivModel):
    id: int
    viewable: bool
    content_order: int = Field(alias="contentOrder")
    title: str
    cover_url: UrlType | None = None
    viewable_massage: str | None = None


class NovelSeriesNavigation(PixivModel):
    next: NovelSeriesNavigationNovel | None = Field(None, alias="nextNovel")
    prev: NovelSeriesNavigationNovel | None = Field(None, alias="prevNovel")


class NovelSeries(PixivModel):
    id: int
    title: str
    is_watched: bool | None = None
    navigation: NovelSeriesNavigation | None = None


class Novel(PixivModel):
    id: int
    title: str
    caption: str | None = None
    restrict: int
    x_restrict: int
    is_original: bool
    image_urls: ImageUrl
    create_date: Datetime
    tags: list[Tag]
    page_count: int
    text_length: int
    user: User
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

    async def get_text(self) -> "NovelText":
        return await self._pixiv_client.NOVEL.text(self.id)


class NovelRating(PixivModel):
    like: int
    bookmark: int
    view: int


class NovelGlossaryItem(PixivModel):
    id: int
    name: str
    overview: str
    cover: ImageUrl | None = None


class NovelImageUrl(PixivImage):
    mw240: UrlType = Field(alias="240mw")
    mw480: UrlType = Field(alias="480mw")
    square1200: UrlType = Field(alias="1200x1200")
    square128: UrlType = Field(alias="128x128")
    original: UrlType

    @property
    def link(self) -> UrlType:
        return self.original


class NovelImage(PixivModel):
    id: int
    sl: int
    urls: NovelImageUrl


class NovelIllustUser(PixivModel):
    id: int
    name: str
    image: UrlType


class NovelIllust(PixivModel):
    id: int
    visible: bool
    message: str | None = Field(None, alias="availableMessage")
    user: NovelIllustUser
    page: int
    title: str
    description: str | None = None
    restrict: int
    x_restrict: int = Field(alias="xRestrict")
    sl: int
    tags: list[Tag]
    images: ImageUrl


class NovelText(PixivModel):
    id: int
    user_id: int = Field(alias="userId")
    title: str
    series: NovelSeries
    cover_url: UrlType = Field(alias="coverUrl")
    tags: list[Tag]
    caption: str | None = None
    # noinspection SpellCheckingInspection
    create_date: datetime.date = Field(alias="cdate")
    rating: NovelRating
    text: str
    illusts: list[NovelIllust] | None = None
    images: list[NovelImage] | None = None
    ai_type: int = Field(alias="aiType")
    is_original: bool = Field(alias="isOriginal")
    glossary_items: list[NovelGlossaryItem] = Field(alias="glossaryItems")
