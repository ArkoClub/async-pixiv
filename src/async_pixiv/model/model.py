from datetime import datetime
from enum import Enum
from typing import (
    List,
    Optional,
)

from pydantic import (
    EmailStr,
    HttpUrl,
)

from async_pixiv.model._base import PixivModel


class Artwork(PixivModel):
    class PageUrl(PixivModel):
        original_image_url: HttpUrl

    class MetaPage(PixivModel):
        image_urls: "ImageUrl"

    id: int
    title: str
    type: "ArtworkType"
    img_urls: List["ImageUrl"]
    caption: str
    restrict: int
    user: "User"
    tags: List["Tag"]
    tools: List[str]
    create_data: datetime
    page_count: int
    width: int
    height: int
    sanity_level: int
    x_restrict: int
    # series: Optional
    meta_single_page: PageUrl
    meta_pages: List[MetaPage]
    total_view: int
    total_bookmarks: int
    is_bookmarked: bool
    visible: bool
    is_muted: bool
    total_comments: int
    comment_access_control: int


class UgoiraMetadata(PixivModel):
    class ZipUrls(PixivModel):
        medium: HttpUrl

    class Frame(PixivModel):
        file: str
        delay: int

    zip_urls: ZipUrls
    frames: List[Frame]


class User(PixivModel):
    id: int
    name: str
    account: str
    profile_image_urls: "ProfileImg"
    is_followed: Optional[bool]
    is_premium: Optional[bool]
    is_mail_authorized: Optional[bool]
    x_restrict: Optional[int]
    mail_address: Optional[EmailStr]


class Tag(PixivModel):
    name: str
    translated_name: Optional[str]


class Comment(PixivModel):
    id: int
    comment: str
    date: datetime
    user: "User"
    parent_comment: Optional["Comment"]


class NovelSeries(PixivModel):
    id: int
    title: str


class Novel(PixivModel):
    id: int
    title: str
    caption: str
    restrict: int
    x_restrict: int
    is_original: bool
    image_urls: "ImageUrl"
    create_date: datetime
    tags: List["Tag"]
    page_count: int
    text_length: int
    user: "User"
    series: Optional["NovelSeries"]
    is_bookmarked: bool
    total_bookmarks: int
    total_view: int
    visible: bool
    total_comments: int
    is_muted: bool
    # noinspection SpellCheckingInspection
    is_mypixiv_only: bool
    is_x_restricted: bool
    comment_access_control: int


class ProfileImg(PixivModel):
    medium: Optional[HttpUrl]
    px_16x16: Optional[HttpUrl]
    px_50x50: Optional[HttpUrl]
    px_170x170: Optional[HttpUrl]


class ImageUrl(PixivModel):
    square_medium: HttpUrl
    medium: HttpUrl
    large: HttpUrl
    original: Optional[HttpUrl]


class ArtworkType(Enum):
    illust = 'illust'
    ugoira = 'ugoira'
    manga = 'manga'


class Profile(PixivModel):
    webpage: HttpUrl
    gender: str
    birth: str
    birth_day: str
    birth_year: int
    region: str
    address_id: int
    country_code: str
    job: str
    job_id: int
    total_follow_users: int
    # noinspection SpellCheckingInspection
    total_mypixiv_users: int
    total_illusts: int
    total_manga: int
    total_novels: int
    total_illust_bookmarks_public: int
    total_illust_series: int
    total_novel_series: int
    background_image_url: HttpUrl
    twitter_account: str
    twitter_url: HttpUrl
    pawoo_url: Optional[HttpUrl]
    is_premium: bool
    is_using_custom_profile_image: bool


class ProfilePublicity(PixivModel):
    class Choice(Enum):
        public = 'public'

    gender: Choice
    region: Choice
    birth_day: Choice
    birth_year: Choice
    job: Choice
    pawoo: Choice


class WorkSpace(PixivModel):
    pc: Optional[str]
    monitor: Optional[str]
    tool: Optional[str]
    scanner: Optional[str]
    tablet: Optional[str]
    mouse: Optional[str]
    printer: Optional[str]
    desktop: Optional[str]
    music: Optional[str]
    desk: Optional[str]
    chair: Optional[str]
    comment: Optional[str]
    workspace_image_url: Optional[HttpUrl]
