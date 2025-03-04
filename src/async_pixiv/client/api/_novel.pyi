from typing import Sequence

from async_pixiv.client.api._abc import APIBase
from async_pixiv.model import PixivModel
from async_pixiv.model.novel import Novel, NovelText
from async_pixiv.model.other.enums import SearchAIType, SearchShort, SearchTarget
from async_pixiv.model.other.result import PageResult
from async_pixiv.typedefs import DurationTypes, ShortTypes

__all__ = ("NovelAPI", "NovelPageResult")

class NovelDetail(PixivModel):
    novel: Novel

class NovelPageResult(PageResult[Novel]):
    previews: list[Novel]

class NovelAPI(APIBase):
    async def __call__(self, id: int) -> NovelDetail:
        pass

    async def search(
        self,
        words: str | Sequence[str],
        *,
        sort: ShortTypes = SearchShort.DateDecrease,
        duration: DurationTypes | None = None,
        target: SearchTarget | None = SearchTarget.TAGS_PARTIAL,
        offset: int | None = None,
        search_ai_type: SearchAIType | None = None,
        merge_plain_keyword_results: bool = True,
        include_translated_tag_results: bool = True,
        **kwargs,
    ) -> NovelPageResult:
        pass

    async def detail(self, id: int) -> NovelDetail:
        pass

    async def recommended(self) -> NovelPageResult:
        pass

    async def text(self, id: int, *, viewer_version: str = "20221031_ai") -> NovelText:
        pass
