from pydantic import Field

# noinspection PyProtectedMember
from async_pixiv._compat import json_loads, re
from async_pixiv.client.api._abc import APIBase
from async_pixiv.const import APP_API_HOST
from async_pixiv.model import PixivModel
from async_pixiv.model.novel import Novel, NovelText
from async_pixiv.model.other.enums import SearchFilter, SearchShort, SearchTarget
from async_pixiv.model.other.result import PageResult

__all__ = ("NovelAPI", "NovelDetail", "NovelPageResult")


class NovelDetail(PixivModel):
    novel: Novel


class NovelPageResult(PageResult[Novel]):
    previews: list[Novel] = Field([], alias="novels")


class NovelAPI(APIBase):
    _detail_model = NovelDetail
    _page_result_model = NovelPageResult

    async def search(
        self,
        words,
        *,
        sort=SearchShort.DateDecrease,
        duration=None,
        target=SearchTarget.TAGS_PARTIAL,
        offset=None,
        search_ai_type=None,
        merge_plain_keyword_results=True,
        include_translated_tag_results=True,
        **kwargs,
    ) -> NovelPageResult:
        # noinspection PyTypeChecker
        return await super().search(
            words,
            sort=sort,
            duration=duration,
            target=target,
            offset=offset,
            search_ai_type=search_ai_type,
            merge_plain_keyword_results=merge_plain_keyword_results,
            include_translated_tag_results=include_translated_tag_results,
            **kwargs,
        )

    # noinspection PyShadowingBuiltins
    async def detail(self, id):
        response = await self._pixiv_client.request_get(
            APP_API_HOST / f"v2/{self.type}/detail",
            params={f"{self.type}_id": id, "filter": SearchFilter.ANDROID},
        )
        response.raise_for_status().raise_for_result()
        return NovelDetail.model_validate(
            response.json(),
            _pixiv_client=self._pixiv_client,
        )

    # noinspection PyShadowingBuiltins
    async def text(self, id, *, viewer_version="20221031_ai"):
        response = await self._pixiv_client.request_get(
            APP_API_HOST / "webview/v2/novel",
            params={"id": id, "viewer_version": viewer_version},
        )
        response.raise_for_status().raise_for_result()
        json_content = (
            re.search(r"novel:\s({.+}),\s+isOwnWork", response.text)
            .groups()[0]
            .encode()
        )
        json_data = json_loads(json_content)

        json_data["series"] = {
            "id": json_data["seriesId"],
            "title": json_data["seriesTitle"],
            "is_watched": json_data["seriesIsWatched"],
            "navigation": json_data["seriesNavigation"],
        }

        json_data["tags"] = [{"name": tag} for tag in json_data["tags"]]
        json_data["illusts"] = (
            [
                {k: v for k, v in illust.items() if k != "illust"}
                | {k: v for k, v in illust["illust"].items() if k != "tags"}
                | {
                    "tags": [
                        {
                            "name": tag["tag"],
                            "userId": tag["userId"],
                        }
                        for tag in illust["illust"]["tags"]
                    ]
                }
                for illust in json_data["illusts"].values()
            ]
            if json_data["illusts"]
            else []
        )
        json_data["images"] = list(
            json_data["images"].values() if json_data["images"] else []
        )
        return NovelText.model_validate(
            json_data,
            _pixiv_client=self._pixiv_client,
        )
