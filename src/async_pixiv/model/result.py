from typing import (
    List,
    Optional,
Iterator
)

from pydantic import HttpUrl,Field

from async_pixiv.model._base import PixivModel
from async_pixiv.model.artwork import ArtWork
from async_pixiv.model.user import (
    User,
    UserProfile,
    UserProfilePublicity,
    UserWorkSpace,
)


class UserPreview(PixivModel):
    user: User
    illusts: List[ArtWork]
    is_muted: bool


class UserSearchResult(PixivModel):
    user_list: List[UserPreview] = Field(alias='user_previews')
    next_url: Optional[HttpUrl]

    def __iter__(self) -> Iterator[UserPreview]:
        return iter(self.user_list)


class UserDetailResult(PixivModel):
    user: User
    profile: UserProfile
    profile_publicity: UserProfilePublicity
    workspace: UserWorkSpace
