from typing import (
    Optional,
    TYPE_CHECKING,
)

from pydantic import HttpUrl

from async_pixiv.model._base import PixivModel
from async_pixiv.model.other import ImageUrl

if TYPE_CHECKING:
    from async_pixiv.client import PixivClient
    from async_pixiv.model.result import (
        UserDetailResult,
        UserIllustsResult,
        UserBookmarksIllustsResult,
        UserRelatedResult,
    )


# noinspection PyProtectedMember
class User(PixivModel):
    id: int
    name: str
    account: str
    profile_image_urls: ImageUrl
    is_followed: Optional[bool]
    comment: Optional[str]

    async def detail(
            self, client: Optional["PixivClient"] = None, *,
            for_ios: bool = True
    ) -> "UserDetailResult":
        from async_pixiv.client._section import SearchFilter

        if client is None:
            from async_pixiv.client import PixivClient
            client = PixivClient.get_client()

        return await client.USER.detail(
            self.id,
            filter=SearchFilter.ios if for_ios else SearchFilter.android
        )

    async def illusts(
            self, client: Optional["PixivClient"] = None, *,
            for_ios: bool = True, offset: Optional[int] = None
    ) -> "UserIllustsResult":
        from async_pixiv.client._section import SearchFilter

        if client is None:
            from async_pixiv.client import PixivClient
            client = PixivClient.get_client()
        return await client.USER.illusts(
            self.id, offset=offset,
            filter=SearchFilter.ios if for_ios else SearchFilter.android,
        )

    async def bookmarks(
            self, client: Optional["PixivClient"] = None, *,
            for_ios: bool = True, tag: Optional[str] = None,
            max_bookmark_id: Optional[int] = None,
    ) -> "UserBookmarksIllustsResult":
        from async_pixiv.client._section import SearchFilter

        if client is None:
            from async_pixiv.client import PixivClient
            client = PixivClient.get_client()
        return await client.USER.bookmarks(
            self.id, tag=tag, max_bookmark_id=max_bookmark_id,
            filter=SearchFilter.ios if for_ios else SearchFilter.android,
        )

    async def related(
            self, client: Optional["PixivClient"] = None, *,
            for_ios: bool = True, offset: Optional[int] = None
    ) -> "UserRelatedResult":
        from async_pixiv.client._section import SearchFilter

        if client is None:
            from async_pixiv.client import PixivClient
            client = PixivClient.get_client()
        return await client.USER.related(
            self.id, offset=offset,
            filter=SearchFilter.ios if for_ios else SearchFilter.android,
        )


class UserProfile(PixivModel):
    webpage: Optional[HttpUrl]
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
    background_image_url: Optional[HttpUrl]
    twitter_account: Optional[str]
    twitter_url: Optional[HttpUrl]
    pawoo_url: Optional[HttpUrl]
    is_premium: bool
    is_using_custom_profile_image: bool


class UserProfilePublicity(PixivModel):
    gender: str
    region: str
    birth_day: str
    birth_year: str
    job: str
    pawoo: bool


class UserWorkSpace(PixivModel):
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
