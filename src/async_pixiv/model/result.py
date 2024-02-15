from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    AsyncIterator,
    Generic,
    Iterator,
    Optional,
    TypeVar,
)

from pydantic import (
    AnyHttpUrl,
    Field,
)
from typing_extensions import Annotated, Self

from async_pixiv.model._base import NullDictValidator, PixivModel
from async_pixiv.model.illust import Comment, Illust, UgoiraMetadata
from async_pixiv.model.novel import (
    Novel,
    NovelMaker,
    NovelSeries,
)
from async_pixiv.model.user import (
    User,
    UserProfile,
    UserProfilePublicity,
    UserWorkSpace,
)
from async_pixiv.utils.context import set_pixiv_client

__all__ = [
    "UserPreview",
    "UserSearchResult",
    "UserIllustsResult",
    "UserBookmarksIllustsResult",
    "UserNovelsResult",
    "UserDetailResult",
    "UserRelatedResult",
    "IllustSearchResult",
    "IllustDetailResult",
    "IllustCommentResult",
    "IllustRelatedResult",
    "IllustNewResult",
    "UgoiraMetadataResult",
    "RecommendedResult",
    "NovelSearchResult",
    "NovelContentResult",
    "NovelSeriesResult",
    "NovelDetailResult",
]

T = TypeVar("T")


class PageResult(ABC, PixivModel, Generic[T]):
    next_url: AnyHttpUrl | None = None
    search_span_limit: int | None = None

    @abstractmethod
    def __iter__(self) -> Iterator[T]:
        pass

    async def next(self) -> Optional[Self]:
        if getattr(self, "next_url", None):
            data = (await self._pixiv_client.get(self.next_url)).json()
            with set_pixiv_client(self._pixiv_client):
                return self.__class__.parse_obj(data)
        else:
            return None

    async def iter_all_pages(self) -> AsyncIterator[T]:
        for result in self:
            yield result
        next_results = await self.next()
        while next_results is not None:
            for result in next_results:
                yield result
            next_results = await next_results.next()


class UserPreview(PixivModel):
    user: User
    illusts: list[Illust]
    is_muted: bool


class UserSearchResult(PageResult[UserPreview]):
    user_previews: list[UserPreview] = Field([], alias="user_previews")

    def __iter__(self) -> Iterator[UserPreview]:
        return iter(self.user_previews)


class UserIllustsResult(PageResult[Illust]):
    illusts: list[Illust]

    def __iter__(self) -> Iterator[Illust]:
        return iter(self.illusts)


class UserBookmarksIllustsResult(UserIllustsResult):
    pass


class UserNovelsResult(PageResult[Novel]):
    novels: list[Novel] = []

    def __iter__(self) -> Iterator[Novel]:
        return iter(self.novels)


class UserDetailResult(PixivModel):
    user: User
    profile: UserProfile
    profile_publicity: UserProfilePublicity
    workspace: UserWorkSpace


class UserRelatedResult(PixivModel):
    users: list[UserPreview] = Field(alias="user_previews")

    def __iter__(self) -> Iterator[UserPreview]:
        return iter(self.users)


class IllustSearchResult(UserIllustsResult):
    pass


class IllustDetailResult(PixivModel):
    illust: Illust


class IllustCommentResult(PageResult[Comment]):
    total: int = Field(0, alias="total_comments")
    comments: list[Comment] = []
    next_url: AnyHttpUrl | None
    access_comment: bool | None = Field(None, alias="comment_access_control")

    def __iter__(self) -> Iterator[Comment]:
        return iter(self.comments)


class IllustRelatedResult(IllustSearchResult):
    pass


class IllustNewResult(IllustDetailResult):
    pass


class UgoiraMetadataResult(PixivModel):
    metadata: UgoiraMetadata = Field(alias="ugoira_metadata")


class RecommendedResult(IllustSearchResult):
    ranking_illusts: list[Illust]
    contest_exists: bool


class NovelSearchResult(UserNovelsResult):
    pass


class NovelDetailResult(PixivModel):
    novel: Novel


class NovelContentResult(PixivModel):
    marker: Annotated[Optional[NovelMaker], NullDictValidator] = Field(
        alias="novel_marker"
    )
    content: str = Field(alias="novel_text")
    previous: Annotated[Optional[Novel], NullDictValidator] = Field(alias="series_prev")
    next: Annotated[Optional[Novel], NullDictValidator] = Field(alias="series_next")

    @property
    def text(self) -> str:
        return self.content


class NovelSeriesResult(NovelSearchResult):
    series: NovelSeries = Field(alias="novel_series_detail")
    first_novel: Novel = Field(alias="novel_series_first_novel")
    latest_novel: Novel = Field(alias="novel_series_latest_novel")
