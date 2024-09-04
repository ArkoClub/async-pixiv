from pydantic import Field

from async_pixiv.client.api._abc import APIBase
from async_pixiv.const import APP_API_HOST
from async_pixiv.model import Illust, PixivModel
from async_pixiv.model.other.enums import SearchShort, SearchTarget
from async_pixiv.model.other.result import PageResult, UgoiraMetadataResult

__all__ = ("IllustAPI", "IllustPageResult", "IllustDetail")

from async_pixiv.utils.context import set_pixiv_client


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

    # noinspection PyShadowingBuiltins
    async def ugoira_metadata(self, id: int) -> UgoiraMetadataResult:
        response = await self._pixiv_client.request_get(
                APP_API_HOST / "v1/ugoira/metadata", params={"illust_id": id}
        )
        response.raise_for_result().raise_for_status()
        with set_pixiv_client(self._pixiv_client):
            return UgoiraMetadataResult.model_validate(response.json())
