from typing import Sequence

from async_pixiv.client.api._abc import APIBase
from async_pixiv.model import PixivModel
from async_pixiv.model.illust import Illust
from async_pixiv.model.novel import Novel
from async_pixiv.model.other.enums import SearchShort
from async_pixiv.model.other.result import PageResult
from async_pixiv.model.user import FullUser, User
from async_pixiv.typedefs import DurationTypes, ShortTypes

__all__ = ("UserAPI", "UserPageResult", "UserPreview", "UserDetail")

UserDetail = FullUser

class UserPreview(PixivModel):
    id: int
    user: User
    illusts: list[Illust]
    novels: list[Novel]
    is_muted: bool

class UserPageResult(PageResult[UserPreview]):
    previews: list[UserPreview]

# noinspection PyShadowingBuiltins
class UserAPI(APIBase):
    async def __call__(self, id: int) -> UserDetail:
        pass

    async def search(
        self,
        words: str | Sequence[str],
        *,
        sort: ShortTypes = SearchShort.DateDecrease,
        duration: DurationTypes | None = None,
        offset: int | None = None,
        **kwargs,
    ) -> UserPageResult:
        pass

    async def detail(self, id: int) -> UserDetail:
        pass

    async def recommended(self) -> UserPageResult:
        pass
