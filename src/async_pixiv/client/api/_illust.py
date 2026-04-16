import datetime
from collections.abc import Sequence

from pydantic import Field

from async_pixiv.client.api._abc import APIBase
from async_pixiv.const import APP_API_HOST
from async_pixiv.model import Illust, PixivModel, SearchAIType
from async_pixiv.model.other.enums import SearchDuration, SearchShort, SearchTarget
from async_pixiv.model.other.result import PageResult, UgoiraMetadataResult
from async_pixiv.typedefs import DurationTypes, ShortTypes

__all__ = ("IllustAPI", "IllustDetail", "IllustPageResult")


class IllustDetail(PixivModel):
    illust: Illust


class IllustPageResult(PageResult[Illust]):
    previews: list[Illust] = Field([], alias="illusts")
    search_span_limit: int = 0
    show_ai: bool = False


class IllustAPI(APIBase[IllustDetail, IllustPageResult]):
    _detail_model = IllustDetail
    _page_result_model = IllustPageResult

    async def __call__(self, id: int) -> IllustDetail:
        return await super().__call__(id)

    async def detail(self, id: int) -> IllustDetail:
        return await super().detail(id)

    async def search(
        self,
        words: str | Sequence[str],
        *,
        sort: ShortTypes = SearchShort.DateDecrease,
        target: SearchTarget | None = SearchTarget.TAGS_PARTIAL,
        search_ai_type: SearchAIType | None = None,
        duration: SearchDuration | DurationTypes | None = None,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
        offset: int | None = None,
        **kwargs,
    ) -> IllustPageResult:
        if start_date is not None and not isinstance(start_date, datetime.date):
            raise TypeError("start_date must be a datetime.date or None")
        if end_date is not None and not isinstance(end_date, datetime.date):
            raise TypeError("end_date must be a datetime.date or None")
        if search_ai_type is not None and not isinstance(search_ai_type, SearchAIType):
            raise TypeError("search_ai_type must be a SearchAIType or None")

        if start_date is not None:
            start_date = start_date.strftime("%Y-%m-%d")
        if end_date is not None:
            end_date = end_date.strftime("%Y-%m-%d")

        if search_ai_type is not None:
            search_ai_type = search_ai_type.value

        # noinspection PyTypeChecker
        return await super().search(
            words,
            sort=sort,
            target=target,
            search_ai_type=search_ai_type,
            duration=duration,
            start_date=start_date,
            end_date=end_date,
            offset=offset,
            **kwargs,
        )

    async def recommended(self) -> IllustPageResult:
        return await super().recommended()

    # noinspection PyShadowingBuiltins
    async def ugoira_metadata(self, id: int) -> UgoiraMetadataResult:
        response = await self._pixiv_client.request_get(
            APP_API_HOST / "v1/ugoira/metadata", params={"illust_id": id}
        )
        response.raise_for_result().raise_for_status()
        return UgoiraMetadataResult.model_validate(
            response.json(),
            _pixiv_client=self._pixiv_client,
        )
