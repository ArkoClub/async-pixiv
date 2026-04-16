from collections.abc import Sequence

from pydantic import Field

from async_pixiv.client.api._abc import APIBase
from async_pixiv.model import PixivModel
from async_pixiv.model.illust import Illust
from async_pixiv.model.novel import Novel
from async_pixiv.model.other.enums import SearchDuration, SearchShort
from async_pixiv.model.other.result import PageResult
from async_pixiv.model.user import FullUser, User
from async_pixiv.typedefs import DurationTypes, ShortTypes

__all__ = ("UserAPI", "UserDetail", "UserPageResult", "UserPreview")

UserDetail = FullUser


class UserPreview(PixivModel):
    user: User
    illusts: list[Illust]
    novels: list[Novel]
    is_muted: bool

    @property
    def id(self) -> int:
        return self.user.id


class UserPageResult(PageResult[UserPreview]):
    previews: list[UserPreview] = Field([], alias="user_previews")


class UserAPI(APIBase[UserDetail, UserPageResult]):
    _detail_model = UserDetail
    _page_result_model = UserPageResult

    async def __call__(self, id: int) -> UserDetail:
        return await super().__call__(id)

    async def detail(self, id: int) -> UserDetail:
        return await super().detail(id)

    async def search(
        self,
        words: str | Sequence[str],
        *,
        sort: ShortTypes = SearchShort.DateDecrease,
        duration: SearchDuration | DurationTypes | None = None,
        offset: int | None = None,
        **kwargs,
    ) -> UserPageResult:
        return await super().search(
            words,
            sort=sort,
            duration=duration,
            offset=offset,
            **kwargs,
        )

    async def recommended(self) -> UserPageResult:
        return await super().recommended()
