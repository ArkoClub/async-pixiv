from datetime import datetime
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Optional,
    TYPE_CHECKING,
    Union,
)
from zipfile import ZipFile

from arkowrapper import ArkoWrapper
from async_pixiv.error import ArtWorkTypeError
from async_pixiv.model._base import (
    PixivModel,
    null_dict_validator,
)
from async_pixiv.model.other import (
    ImageUrl,
    Series,
    Tag,
)
from async_pixiv.model.user import User
from pydantic import (
    AnyHttpUrl,
    Field,
)
from typing_extensions import Literal
from yarl import URL

try:
    import imageio
except ImportError:
    imageio = None

if TYPE_CHECKING:
    from async_pixiv.client import PixivClient
    from async_pixiv.model.result import (
        IllustDetailResult,
        IllustCommentResult,
        IllustRelatedResult,
    )

__all__ = [
    'ArtWork', 'ArtWorkType',
    'Comment',
    'UgoiraMetadata',
]

UGOIRA_RESULT_TYPE = (
    Literal['zip', 'jpg', 'all', 'iter', 'gif']
    if imageio else
    Literal['zip', 'jpg', 'all', 'iter']
)


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


# noinspection PyProtectedMember,PyShadowingBuiltins
class ArtWork(PixivModel):
    class MetaPage(PixivModel):
        image_urls: "ImageUrl"

    class MetaSinglePage(PixivModel):
        original: Optional[AnyHttpUrl] = Field(alias="original_image_url")

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
    meta_single_page: MetaSinglePage
    meta_pages: List[MetaPage]
    total_view: int
    total_bookmarks: int
    is_bookmarked: bool
    visible: bool
    is_muted: bool
    total_comments: Optional[int]
    comment_access_control: Optional[int]

    @property
    def is_nsfw(self) -> bool:
        return self.sanity_level > 5

    @property
    def is_r18(self) -> bool:
        return (
            ArkoWrapper(self.tags)
            .map(lambda x: x.name)
            .append(self.title)
            .map(lambda x: x.upper().replace('-', ''))
            .map(lambda x: 'R18' in x)
            .any()
        )

    @property
    def link(self) -> URL:
        return URL(f"https://www.pixiv.net/artworks/{self.id}/")

    @property
    def all_image_urls(self) -> List[URL]:
        if not self.meta_pages:
            # noinspection PyTypeChecker
            return [self.meta_single_page.original]
        result = []
        for page in self.meta_pages:
            result.append(
                URL(
                    str(
                        page.image_urls.original or page.image_urls.large
                    )
                )
            )
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
            full: bool = False,
            output: Optional[Union[str, Path]] = None,
            client: Optional["PixivClient"] = None
    ) -> List[bytes]:
        if client is None:
            from async_pixiv.client import PixivClient
            client = PixivClient.get_client()
        if not full or not self.meta_pages:
            return [await client.download(
                str(
                    self.meta_single_page.original or
                    self.image_urls.original or
                    self.image_urls.large
                )
            )]
        else:
            result: List[bytes] = []
            for meta_page in self.meta_pages:
                result.append(
                    await client.download(
                        str(
                            meta_page.image_urls.original or
                            meta_page.image_urls.large
                        ), output=output
                    )
                )
            return result

    async def ugoira_metadata(
            self, client: Optional["PixivClient"] = None
    ) -> Optional["UgoiraMetadata"]:
        if self.type != ArtWorkType.ugoira:
            return None
        if client is None:
            from async_pixiv.client import PixivClient
            client = PixivClient.get_client()
        return (await client.ILLUST.ugoira_metadata(self.id)).metadata

    async def download_ugoira(
            self, client: Optional["PixivClient"] = None, *,
            type: UGOIRA_RESULT_TYPE = 'zip'
    ) -> Optional[Union[List[bytes], Dict[str, bytes], Iterator[bytes]]]:
        if self.type != ArtWorkType.ugoira:
            raise ArtWorkTypeError(
                'If you want to download a moving image, '
                'please use this method: \"download\"'
            )
        if client is None:
            from async_pixiv.client import PixivClient
            client = PixivClient.get_client()
        metadata = await self.ugoira_metadata(client)
        zip_url = metadata.zip_url
        data = await client.download(
            zip_url.original or zip_url.large or zip_url.medium,
        )
        if data is None:
            return None
        if type == 'zip':
            return data
        bytes_io = BytesIO(data)
        zip_file = ZipFile(bytes_io)
        frames = []
        for frame_info in metadata.frames:
            with zip_file.open(frame_info.file) as f:
                frames.append(f.read())
        if type == 'jpg':
            return frames
        elif type == 'iter':
            return iter(frames)
        elif imageio and type == 'gif':
            frames = zip(
                frames,
                map(lambda x: '.' + x.file.split('.')[-1], metadata.frames)
            )
            return imageio.v3.imwrite(
                "<bytes>",
                list(
                    map(
                        lambda x: imageio.v3.imread(x[0], extension=x[1]),
                        frames
                    )
                ),
                plugin="pillow",
                extension='.gif',
                duration=list(map(lambda x: x.delay / 1000, metadata.frames)),
                loop=0,
            )
        else:
            return {'zip': data, 'frames': frames}


class Comment(PixivModel):
    id: int
    comment: str
    date: datetime
    user: User
    parent: Optional["Comment"] = Field(alias='parent_comment')

    _check = null_dict_validator('parent')


class UgoiraMetadata(PixivModel):
    class Frame(PixivModel):
        file: str
        delay: int

    zip_url: ImageUrl = Field(alias='zip_urls')
    frames: List[Frame]
