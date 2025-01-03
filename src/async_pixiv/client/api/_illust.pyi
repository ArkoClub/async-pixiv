import datetime
from typing import Sequence

from async_pixiv.client.api._abc import APIBase
from async_pixiv.model import Illust, PixivModel
from async_pixiv.model.other.enums import SearchAIType, SearchShort, SearchTarget
from async_pixiv.model.other.result import PageResult, UgoiraMetadataResult
from async_pixiv.typedefs import DurationTypes, ShortTypes

__all__ = ("IllustAPI", "IllustPageResult", "IllustDetail")

class IllustDetail(PixivModel):
    illust: Illust

class IllustPageResult(PageResult[Illust]):
    previews: list[Illust]
    search_span_limit: int
    show_ai: bool

class IllustAPI(APIBase):
    async def __call__(self, id: int) -> IllustDetail:
        pass
    async def detail(self, id: int) -> IllustDetail:
        pass
    async def search(
        self,
        words: str | Sequence[str],
        *,
        sort: ShortTypes = SearchShort.DateDecrease,
        target: SearchTarget | None = SearchTarget.TAGS_PARTIAL,
        search_ai_type: SearchAIType | None = None,
        duration: DurationTypes | None = None,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
        offset: int | None = None,
        **kwargs,
    ) -> IllustPageResult:
        pass
    async def recommended(self) -> IllustPageResult:
        pass
    async def ugoira_metadata(self, id: int) -> UgoiraMetadataResult:
        pass
