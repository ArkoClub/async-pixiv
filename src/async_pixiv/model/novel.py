from datetime import datetime
from typing import (
    List,
    Optional,
    TYPE_CHECKING,
)

from pydantic import (
    Extra,
    Field,
    PrivateAttr,
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
        NovelDetailResult,
        NovelSeriesResult,
    )

__all__ = ["Novel", "NovelMaker", "NovelSeries"]


# noinspection PyProtectedMember
class Novel(PixivModel):
    id: int
    title: str
    caption: str
    restrict: int
    x_restrict: int
    is_original: bool
    image_url: ImageUrl = Field(alias="image_urls")
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
    ai_type: AIType = Field(alias="novel_ai_type")

    _check = null_dict_validator("series")
    _is_r18: Optional[bool] = PrivateAttr(None)
    _lang: Optional[str] = PrivateAttr(None)

    @property
    def link(self) -> URL:
        return URL(f"https://www.pixiv.net/novel/show.php?id={self.id}")

    async def is_r18(self) -> bool:
        if self._is_r18 is None:
            try:
                client = self._pixiv_client
                response = await client.get(self.link, follow_redirects=True)
                response.raise_for_status()
                html = response.text
                title: str = re.findall(
                    r"<meta property=\"twitter:title\" content=\"(.*?)\">", html
                )[0]
                self._is_r18 = title.startswith("[R-18")
            except HTTPError:
                self._is_r18 = any(
                    map(
                        lambda x: ("R-18" in x.name.upper() or "R18" in x.name.upper()),
                        self.tags,
                    )
                )

        return self._is_r18

    async def get_lang(self) -> str:
        if self._lang is None:
            try:
                client = self._pixiv_client
                response = await client.get(
                    self.link,
                    follow_redirects=True,
                    headers={
                        "user-agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/108.0.0.0 Safari/537.36"
                        ),
                    },
                )
                response.raise_for_status()
                html = response.text
                self._lang = re.findall(r"\"language\":\"(.*?)\",", html)[0]
            except HTTPError:
                pass
        return self._lang

    async def detail(self, *, for_ios: bool = True) -> "NovelDetailResult":
        from async_pixiv.client._section._base import SearchFilter

        return await self._pixiv_client.NOVEL.detail(
            self.id, filter=SearchFilter.ios if for_ios else SearchFilter.android
        )

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

    def __eq__(self, other: "Novel") -> bool:
        if not isinstance(other, Novel):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(f"pixiv_novel_{self.id}")


class NovelMaker(PixivModel):
    page: int

    class Config(PixivModelConfig):
        extra = Extra.allow


class NovelSeries(Series):
    caption: str
    is_original: bool
    is_concluded: bool
    character_count: int = Field(alias="total_character_count")
    user: User
    display: str = Field(alias="display_text")
    watchlist_added: bool
