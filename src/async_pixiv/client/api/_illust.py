from pydantic import Field

from async_pixiv.client.api._abc import APIBase
from async_pixiv.model import Illust, PixivModel
from async_pixiv.model.other.enums import SearchShort, SearchTarget
from async_pixiv.model.other.result import PageResult

__all__ = ("IllustAPI", "IllustPageResult", "IllustDetail")


class IllustDetail(PixivModel):
    illust: Illust


class IllustPageResult(PageResult[Illust]):
    previews: list[Illust] = Field([], alias="illusts")
    search_span_limit: int
    show_ai: bool


class IllustAPI(APIBase):
    async def search(
        self,
        words,
        *,
        sort=SearchShort.DateDecrease,
        duration=None,
        target=SearchTarget.TAGS_PARTIAL,
        offset=None,
        **kwargs,
    ) -> IllustPageResult:
        # noinspection PyTypeChecker
        return await super().search(
            words, sort=sort, duration=duration, target=target, offset=offset, **kwargs
        )
