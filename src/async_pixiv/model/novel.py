from datetime import datetime
from typing import (
    List,
    Optional,
    TYPE_CHECKING,
)

from pydantic import (
    Extra,
    Field, PrivateAttr,
)
from requests import HTTPError
from yarl import URL

from async_pixiv.model._base import (
    PixivModel,
    PixivModelConfig,
    null_dict_validator,
)
from async_pixiv.model.other import (
    AIType,
    ImageUrl,
    Series,
    Tag,
)
from async_pixiv.model.user import User

try:
    import regex as re
except ImportError:
    import re

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
    ai_type: AIType = Field(alias='novel_ai_type')

    _check = null_dict_validator('series')
    _is_r18: Optional[bool] = PrivateAttr(None)

    @property
    def is_nsfw(self) -> bool:
        return self.is_r18

    @property
    def link(self) -> URL:
        return URL(f"https://www.pixiv.net/novel/show.php?id=1{self.id}")

    @property
    def is_r18(self) -> bool:
        if self._is_r18 is None:
            try:
                from async_pixiv.client import PixivClient
                client = PixivClient.get_client()
                response = client.sync_request('GET', str(self.link))
                response.raise_for_status()
                html = response.text
                title: str = re.findall(
                    r"<meta property=\"twitter:title\" content=\"(.*?)\">", html
                )[0]
                self._is_r18 = title.startswith('[R-18')
            except HTTPError:
                self._is_r18 = any(
                    map(
                        lambda x: (
                                'R-18' in x.name.upper()
                                or
                                'R18' in x.name.upper()
                        ),
                        self.tags
                    )
                )

        return self._is_r18

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
