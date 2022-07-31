from datetime import datetime
from enum import Enum
from typing import (
    Dict,
    List,
    Optional,
)

from pydantic import (
    HttpUrl,
)

from async_pixiv.model._base import PixivModel
from async_pixiv.model.other import ImageUrl
from async_pixiv.model.user import User

__all__ = [
    'Tag', 'TagTranslation',
    'ArtWork',
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


class ArtWork(PixivModel):
    class Series(PixivModel):
        id: int
        title: str

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
    meta_pages: List["ImageUrl"]
    total_view: int
    total_bookmarks: int
    is_bookmarked: bool
    visible: bool
    is_muted: bool
    total_comments: Optional[int]
    comment_access_control: Optional[int]
