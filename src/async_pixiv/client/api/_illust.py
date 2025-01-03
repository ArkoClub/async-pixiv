import datetime

from pydantic import Field

from async_pixiv.client.api._abc import APIBase
from async_pixiv.const import APP_API_HOST
from async_pixiv.model import Illust, PixivModel
from async_pixiv.model.other.enums import SearchShort, SearchTarget
from async_pixiv.model.other.result import PageResult, UgoiraMetadataResult
from async_pixiv.utils.context import set_pixiv_client

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
        target=SearchTarget.TAGS_PARTIAL,
        search_ai_type=None,
        duration=None,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
        offset=None,
    ) -> IllustPageResult:
        if start_date is not None and not isinstance(start_date, datetime.date):
            raise TypeError("start_date must be a datetime.date or None")
        if end_date is not None and not isinstance(end_date, (datetime.date, None)):
            raise TypeError("end_date must be a datetime.date or None")

        if start_date is not None:
            start_date = start_date.strftime("%Y-%m-%d")
        if end_date is not None:
            end_date = end_date.strftime("%Y-%m-%d")

        return await super().search(
            words,
            sort=sort,
            target=target,
            search_ai_type=search_ai_type,
            duration=duration,
            start_date=start_date,
            end_date=end_date,
            offset=offset,
        )

    # noinspection PyShadowingBuiltins
    async def ugoira_metadata(self, id: int) -> UgoiraMetadataResult:
        response = await self._pixiv_client.request_get(
            APP_API_HOST / "v1/ugoira/metadata", params={"illust_id": id}
        )
        response.raise_for_result().raise_for_status()
        with set_pixiv_client(self._pixiv_client):
            return UgoiraMetadataResult.model_validate(response.json())
