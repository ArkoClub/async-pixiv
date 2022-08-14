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
    AnyHttpUrl,
    Field,
)
from typing_extensions import Self

from async_pixiv.model._base import (
    PixivModel,
    null_dict_validator,
)
from async_pixiv.model.artwork import (
    ArtWork,
    Comment,
    UgoiraMetadata,
)
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

if TYPE_CHECKING:
    from async_pixiv.client import PixivClient


class PageResult(ABC, PixivModel):
    next_url: Optional[AnyHttpUrl]
    search_span_limit: Optional[int]

    @abstractmethod
    def __iter__(self) -> Iterator:
        pass

    async def next(
            self, client: Optional["PixivClient"] = None
    ) -> Optional[Self]:
        if client is None:
            from async_pixiv.client import PixivClient
            client = PixivClient.get_client()
        if getattr(self, 'next_url', None):
            data = await (await client.get(str(self.next_url))).json()
            return self.__class__.parse_obj(data)
        else:
            return self.__class__()


class UserPreview(PixivModel):
    user: User
    illusts: List[ArtWork]
    is_muted: bool


class UserSearchResult(PageResult):
    users: List[UserPreview] = Field([], alias='user_previews')

    def __iter__(self) -> Iterator[UserPreview]:
        return iter(self.users)


class UserIllustsResult(PageResult):
    illusts: List[ArtWork]

    def __iter__(self) -> Iterator[ArtWork]:
        return iter(self.illusts)


class UserBookmarksIllustsResult(UserIllustsResult):
    pass


class UserNovelsResult(PageResult):
    novels: List[Novel] = []

    def __iter__(self) -> Iterator[Novel]:
        return iter(self.novels)


class UserDetailResult(PixivModel):
    user: User
    profile: UserProfile
    profile_publicity: UserProfilePublicity
    workspace: UserWorkSpace


class UserRelatedResult(PixivModel):
    users: List[UserPreview] = Field(alias='user_previews')

    def __iter__(self) -> Iterator[UserPreview]:
        return iter(self.users)


class IllustSearchResult(UserIllustsResult):
    pass


class IllustDetailResult(PixivModel):
    illust: ArtWork


class IllustCommentResult(PageResult):
    total: int = Field(0, alias='total_comments')
    comments: List[Comment] = []
    next_url: Optional[AnyHttpUrl]
    access_comment: Optional[bool] = Field(alias='comment_access_control')

    def __iter__(self) -> Iterator[Comment]:
        return iter(self.comments)


class IllustRelatedResult(IllustSearchResult):
    pass


class IllustNewResult(IllustDetailResult):
    pass


class UgoiraMetadataResult(PixivModel):
    metadata: UgoiraMetadata = Field(alias="ugoira_metadata")


class RecommendedResult(IllustSearchResult):
    ranking_illusts: List[ArtWork]
    contest_exists: bool


class NovelSearchResult(UserNovelsResult):
    pass


class NovelDetailResult(PixivModel):
    novel: Novel


class NovelContentResult(PixivModel):
    marker: Optional[NovelMaker] = Field(alias='novel_marker')
    content: str = Field(alias='novel_text')
    previous: Optional[Novel] = Field(alias='series_prev')
    next: Optional[Novel] = Field(alias='series_next')

    _check = null_dict_validator('marker', 'previous', 'next')

    @property
    def text(self) -> str:
        return self.content


class NovelSeriesResult(NovelSearchResult):
    series: NovelSeries = Field(alias='novel_series_detail')
    first_novel: Novel = Field(alias='novel_series_first_novel')
    latest_novel: Novel = Field(alias='novel_series_latest_novel')
