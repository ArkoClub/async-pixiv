from pydantic import Field

from async_pixiv.client.api._abc import APIBase
from async_pixiv.model import PixivModel
from async_pixiv.model.illust import Illust
from async_pixiv.model.novel import Novel
from async_pixiv.model.other.result import PageResult
from async_pixiv.model.user import FullUser, User

__all__ = ("UserAPI", "UserPageResult", "UserPreview", "UserDetail")

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


class UserAPI(APIBase):
    pass
