from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
    Union,
)

from pydantic import (
    Field,
    HttpUrl,
    validator,
)
from yarl import URL

from async_pixiv.model._base import PixivModel
from async_pixiv.model.other import ImageUrl
from async_pixiv.model.user import User

if TYPE_CHECKING:
    from async_pixiv.client import PixivClient
    from async_pixiv.model.result import (
        IllustDetailResult,
        IllustCommentResult,
        IllustRelatedResult,
    )

__all__ = [
    'Tag', 'TagTranslation',
    'ArtWork', 'ArtWorkType',
    'Comment',
]


class TagTranslation(PixivModel):
    zh: Optional[str]
    en: Optional[str]


class Tag(PixivModel):
    name: str
    translated_name: Optional[str]


class ArtWorkType(Enum):
    illust = 'illust'
    ugoira = 'ugoira'
    manga = 'manga'
    novel = 'novel'

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ArtWorkType):
            return self.value == other.value
        else:
            try:
                return self.value == str(other)
            except (TypeError, ValueError):
                return False


# noinspection PyProtectedMember
class ArtWork(PixivModel):
    class Series(PixivModel):
        id: int
        title: str

    class MetaPage(PixivModel):
        image_urls: "ImageUrl"

    id: int
    title: str
    type: ArtWorkType
    image_urls: "ImageUrl"
    caption: str
    restrict: int
    user: "User"
    tags: List[Tag]
    tools: List[str]
    create_date: datetime
    page_count: int
    width: int
    height: int
    sanity_level: int
    x_restrict: int
    series: Optional[Series]
    meta_single_page: Dict[str, HttpUrl]
    meta_pages: List[MetaPage]
    total_view: int
    total_bookmarks: int
    is_bookmarked: bool
    visible: bool
    is_muted: bool
    total_comments: Optional[int]
    comment_access_control: Optional[int]

    @property
    def is_r18(self) -> bool:
        if len(self.tags) >= 1:
            return self.tags[0].name.title().replace('-', '') == 'R18'
        return False

    @property
    def link(self) -> URL:
        return URL(f"https://www.pixiv.net/artworks/{self.id}/")

    @property
    def all_image_urls(self) -> List[URL]:
        result = []
        for page in self.meta_pages:
            result.append(URL(str(
                page.image_urls.original or page.image_urls.large
            )))
        return result

    async def detail(
            self, client: Optional["PixivClient"] = None, *,
            for_ios: bool = True
    ) -> "IllustDetailResult":
        from async_pixiv.client._section import SearchFilter

        if client is None:
            from async_pixiv.client import PixivClient
            client = PixivClient.get_client()

        return await client.ILLUST.detail(
            self.id,
            filter=SearchFilter.ios if for_ios else SearchFilter.android
        )

    async def comments(
            self, client: Optional["PixivClient"] = None, *,
            offset: Optional[int] = None
    ) -> "IllustCommentResult":
        if client is None:
            from async_pixiv.client import PixivClient
            client = PixivClient.get_client()
        return await client.ILLUST.comments(self.id, offset=offset)

    async def related(
            self, client: Optional["PixivClient"] = None, *,
            for_ios: bool = True,
            offset: Optional[int] = None,
            seed_id: Optional[int] = None
    ) -> "IllustRelatedResult":
        from async_pixiv.client._section import SearchFilter
        if client is None:
            from async_pixiv.client import PixivClient
            client = PixivClient.get_client()
        return await client.ILLUST.related(
            self.id, offset=offset, seed_ids=seed_id,
            filter=SearchFilter.ios if for_ios else SearchFilter.android
        )

    async def download(
            self, *,
            output: Optional[Union[str, Path]] = None,
            client: Optional["PixivClient"] = None
    ) -> Optional[bytes]:
        if client is None:
            from async_pixiv.client import PixivClient
            client = PixivClient.get_client()
        url = str(self.image_urls.original or self.image_urls.large)
        return await client.download(url, output=output)


class Comment(PixivModel):
    id: int
    comment: str
    date: datetime
    user: User
    parent: Optional["Comment"] = Field(alias='parent_comment')

    @validator('parent', pre=True, always=True)
    def parent_check(cls, value):
        if value == {}:
            return None
        else:
            return value
