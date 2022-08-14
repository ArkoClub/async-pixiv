from datetime import datetime
from typing import (
    List,
    Optional,
    TYPE_CHECKING,
)

from pydantic import (
    Extra,
    Field,
)

from async_pixiv.model._base import (
    PixivModel,
    PixivModelConfig,
    null_dict_validator,
)
from async_pixiv.model.other import (
    ImageUrl,
    Series,
    Tag,
)
from async_pixiv.model.user import User

if TYPE_CHECKING:
    from async_pixiv.client import PixivClient
    from async_pixiv.model.result import (
        NovelContentResult,
        NovelSeriesResult,
    )

__all__ = ['Novel', 'NovelMaker', 'NovelSeries']


class Novel(PixivModel):
    id: int
    title: str
    caption: str
    restrict: int
    x_restrict: int
    is_original: bool
    image_url: ImageUrl = Field(alias='image_urls')
    create_date: datetime
    tags: List[Tag]
    page_count: int
    text_length: int
    user: User
    series: Optional[Series]
    is_bookmarked: bool
    total_bookmarks: int
    total_view: int
    visible: bool
    total_comments: int
    is_muted: bool
    is_mypixiv_only: bool
    is_x_restricted: bool
    comment_access_control: Optional[int]

    _check = null_dict_validator('series')

    async def content(
            self, client: Optional["PixivClient"] = None
    ) -> "NovelContentResult":
        if client is None:
            from async_pixiv.client import PixivClient
            client = PixivClient.get_client()
        return await client.NOVEL.content(self.id)

    async def series_detail(
            self, client: Optional["PixivClient"] = None
    ) -> Optional["NovelSeriesResult"]:
        if self.series is None:
            return None
        if client is None:
            from async_pixiv.client import PixivClient
            client = PixivClient.get_client()
        return await client.NOVEL.series(self.series.id)


class NovelMaker(PixivModel):
    page: int

    class Config(PixivModelConfig):
        extra = Extra.allow


class NovelSeries(Series):
    caption: str
    is_original: bool
    is_concluded: bool
    character_count: int = Field(alias='total_character_count')
    user: User
    display: str = Field(alias='display_text')
    watchlist_added: bool
