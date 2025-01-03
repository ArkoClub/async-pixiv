from pydantic import Field

# noinspection PyProtectedMember
from async_pixiv.client.api._abc import APIBase
from async_pixiv.const import APP_API_HOST
from async_pixiv.model import PixivModel
from async_pixiv.model.novel import Novel
from async_pixiv.model.other.enums import SearchShort, SearchTarget
from async_pixiv.model.other.result import PageResult

__all__ = ("NovelAPI", "NovelPageResult", "NovelDetail")


class NovelDetail(PixivModel):
    novel: Novel


class NovelPageResult(PageResult[Novel]):
    previews: list[Novel] = Field([], alias="novels")


class NovelAPI(APIBase):
    async def search(
        self,
        words,
        *,
        sort=SearchShort.DateDecrease,
        duration=None,
        target=SearchTarget.TAGS_PARTIAL,
        offset=None,
        **kwargs,
    ) -> NovelPageResult:
        # noinspection PyTypeChecker
        return await super().search(
            words, sort=sort, duration=duration, target=target, offset=offset, **kwargs
        )

    # noinspection PyShadowingBuiltins
    async def detail(self, id):
        # noinspection PyProtectedMember
        from async_pixiv.model.other.enums import SearchFilter
        from async_pixiv.utils.context import set_pixiv_client

        response = await self._pixiv_client.request_get(
            APP_API_HOST / f"v2/{self._type}/detail",
            params={f"{self._type}_id": id, "filter": SearchFilter.ANDROID},
        )
        response.raise_for_status().raise_for_result()

        with set_pixiv_client(self._pixiv_client):
            return NovelDetail.model_validate(response.json())
