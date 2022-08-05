from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    Iterator,
    List,
    Optional,
    TYPE_CHECKING,
)

from pydantic import (
    Field,
    HttpUrl,
)
from typing_extensions import Self

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

if TYPE_CHECKING:
    from async_pixiv.client import PixivClient


class SearchResult(ABC, PixivModel):
    next_url: Optional[HttpUrl]
    search_span_limit: Optional[int]

    @abstractmethod
    def __iter__(self) -> Iterator:
        pass

    async def next(self, client: Optional["PixivClient"] = None) -> Self:
        if client is None:
            from async_pixiv.client import PixivClient
            client = PixivClient.get_client()
        data = await (await client.get(str(self.next_url))).json()
        return self.__class__.parse_obj(data)


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


class IllustCommentResult(SearchResult):
    total: int = Field(alias='total_comments')
    comments: List[Comment]
    next_url: Optional[HttpUrl]
    access_comment: Optional[bool] = Field(alias='comment_access_control')

    def __iter__(self) -> Iterator[Comment]:
        return iter(self.comments)


class IllustRelatedResult(IllustSearchResult):
    pass
