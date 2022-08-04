from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    Iterator,
    List,
    Optional,
)

from pydantic import (
    Field,
    HttpUrl,
)

from async_pixiv.model._base import PixivModel
from async_pixiv.model.artwork import (
    ArtWork,
    Comment,
)
from async_pixiv.model.user import (
    User,
    UserProfile,
    UserProfilePublicity,
    UserWorkSpace,
)


class SearchResult(ABC, PixivModel):
    next_url: Optional[HttpUrl]
    search_span_limit: Optional[int]

    @abstractmethod
    def __iter__(self) -> Iterator: pass


class UserPreview(PixivModel):
    user: User
    illusts: List[ArtWork]
    is_muted: bool


class UserSearchResult(SearchResult):
    users: List[UserPreview] = Field(alias='user_previews')

    def __iter__(self) -> Iterator[UserPreview]:
        return iter(self.users)


class UserIllustsResult(PixivModel):
    illusts: List[ArtWork]
    next_url: Optional[HttpUrl]


class UserBookmarksIllustsResult(UserIllustsResult):
    pass


class UserDetailResult(PixivModel):
    user: User
    profile: UserProfile
    profile_publicity: UserProfilePublicity
    workspace: UserWorkSpace


class UserRelatedResult(PixivModel):
    users: List[UserPreview] = Field(alias='user_previews')

    def __iter__(self) -> Iterator[UserPreview]:
        return iter(self.users)


class IllustSearchResult(SearchResult):
    illusts: List[ArtWork]

    def __iter__(self) -> Iterator[ArtWork]:
        return iter(self.illusts)


class IllustDetailResult(PixivModel):
    illust: ArtWork


class IllustCommentResult(PixivModel):
    total: int = Field(alias='total_comments')
    comments: List[Comment]
    next_url: Optional[HttpUrl]
    access_comment: Optional[bool] = Field(alias='comment_access_control')


class IllustRelatedResult(IllustSearchResult):
    pass
