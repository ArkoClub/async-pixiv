from asyncio import Event
from datetime import datetime
from enum import Enum
from functools import cached_property
from io import BytesIO
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING, Union, overload
from zipfile import ZipFile

from aiofiles import open as async_open

# noinspection PyUnresolvedReferences
from aiofiles.tempfile import TemporaryDirectory
from pydantic import (
    AnyHttpUrl,
    Field,
    PrivateAttr,
)
from requests import HTTPError, Session
from typing_extensions import Annotated, Literal
from yarl import URL

from async_pixiv.const import AJAX_HOST
from async_pixiv.error import ArtWorkTypeError
from async_pixiv.model._base import NullDictValidator, PixivModel
from async_pixiv.model.other import (
    AIType,
    ImageUrl,
    Series,
    Tag,
)
from async_pixiv.model.user import User
from async_pixiv.typedefs import UGOIRA_RESULT_TYPE
from async_pixiv.utils.context import get_pixiv_client
from async_pixiv.utils.ffmpeg import FFmpeg

try:
    import regex as re
except ImportError:
    import re

if TYPE_CHECKING:
    from async_pixiv.client import PixivClient
    from async_pixiv.model.result import (
        IllustDetailResult,
        IllustCommentResult,
        IllustRelatedResult,
    )

__all__ = [
    "Illust",
    "IllustType",
    "Comment",
    "UgoiraMetadata",
]

session = Session()


class IllustType(Enum):
    illust = "illust"
    ugoira = "ugoira"
    manga = "manga"
    novel = "novel"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, IllustType):
            return self.value == other.value
        else:
            try:
                return self.value == str(other)
            except (TypeError, ValueError):
                return False


class IllustMetaPage(PixivModel):
    image_urls: "ImageUrl"


class IllustMetaSinglePage(PixivModel):
    original: AnyHttpUrl | None = Field(None, alias="original_image_url")

    @property
    def link(self):
        return self.original


# noinspection PyProtectedMember,PyShadowingBuiltins
class Illust(PixivModel):
    id: int
    title: str
    type: IllustType
    image_urls: "ImageUrl"
    caption: str
    restrict: int
    user: "User"
    tags: list[Tag]
    tools: list[str]
    create_date: datetime
    page_count: int
    width: int
    height: int
    sanity_level: int
    x_restrict: int
    series: Series | None = None
    meta_single_page: IllustMetaSinglePage
    meta_pages: list[IllustMetaPage]
    total_view: int
    total_bookmarks: int
    is_bookmarked: bool
    visible: bool
    is_muted: bool
    total_comments: int | None = None
    comment_access_control: int | None = None
    ai_type: AIType = Field(alias="illust_ai_type")

    _ugoira_metadata: Optional["UgoiraMetadata"] = PrivateAttr(None)
    _is_r18: bool | None = PrivateAttr(None)
    _is_r18g: bool | None = PrivateAttr(None)

    @cached_property
    def link(self) -> URL:
        return URL(f"https://www.pixiv.net/artworks/{self.id}/")

    @cached_property
    def is_nsfw(self) -> bool:
        return self.sanity_level > 5

    async def is_r18(self) -> bool:
        if self._is_r18 is None:
            try:
                client = self._pixiv_client
                response = await client.get(
                    f"https://www.pixiv.net/ajax/illust/{self.id}",
                    follow_redirects=True,
                )
                response.raise_for_status()
                self._is_r18 = "R-18" in list(
                    map(lambda x: x["tag"], response.json()["body"]["tags"]["tags"])
                )
            except HTTPError:
                self._is_r18 = any(
                    map(
                        lambda x: ("R18" in x.name.replace("-", "").upper()),
                        self.tags,
                    )
                )

        return self._is_r18

    async def is_r18g(self) -> bool:
        if self._is_r18g is None:
            try:
                client = self._pixiv_client
                response = await client.get(
                    AJAX_HOST / f"illust/{self.id}",
                    follow_redirects=True,
                )
                response.raise_for_status()
                json_data = response.json(raise_for_status=True)["body"]
                self._is_r18g = "R-18G" in [i["tag"] for i in json_data["tags"]["tags"]]
            except HTTPError:
                self._is_r18g = any(
                    map(
                        lambda x: ("R18G" in x.name.replace("-", "").upper()),
                        self.tags,
                    )
                )
        return self._is_r18g

    @cached_property
    def all_image_urls(self) -> list[URL]:
        if not self.meta_pages:
            # noinspection PyTypeChecker
            return [self.meta_single_page.original]
        result = []
        for page in self.meta_pages:
            result.append(URL(page.image_urls.link))
        return result

    async def detail(self, *, for_ios: bool = True) -> "IllustDetailResult":
        from async_pixiv.client._section._base import SearchFilter

        return await self._pixiv_client.ILLUST.detail(
            self.id, filter=SearchFilter.ios if for_ios else SearchFilter.android
        )

    async def comments(self, *, offset: int | None = None) -> "IllustCommentResult":
        return await self._pixiv_client.ILLUST.comments(self.id, offset=offset)

    async def related(
        self,
        *,
        for_ios: bool = True,
        offset: int | None = None,
        seed_id: int | None = None,
    ) -> "IllustRelatedResult":
        from async_pixiv.client._section._base import SearchFilter

        return await self._pixiv_client.ILLUST.related(
            self.id,
            offset=offset,
            seed_ids=seed_id,
            filter=SearchFilter.ios if for_ios else SearchFilter.android,
        )

    async def download(
        self,
        *,
        full: bool = False,
        output: Optional[Union[str, Path]] = None,
        client: Optional["PixivClient"] = None,
    ) -> list[bytes]:
        client = client or get_pixiv_client(True)
        if not full or not self.meta_pages:
            return [
                await client.download(
                    self.meta_single_page.link or self.image_urls.link
                )
            ]
        else:
            result: list[bytes] = []
            for meta_page in self.meta_pages:
                result.append(
                    await client.download(meta_page.image_urls.link, output=output)
                )
            return result

    async def ugoira_metadata(self) -> Optional["UgoiraMetadata"]:
        if self.type != IllustType.ugoira:
            return None
        if self._ugoira_metadata is None:
            self._ugoira_metadata = (
                await self._pixiv_client.ILLUST.ugoira_metadata(self.id)
            ).metadata
        return self._ugoira_metadata

    @overload
    async def download_ugoira(self, *, type: Literal["zip"]) -> Optional[bytes]:
        """type of zip"""

    @overload
    async def download_ugoira(self, *, type: Literal["all"]) -> Optional[list[bytes]]:
        """type of all"""

    @overload
    async def download_ugoira(self, *, type: Literal["gif"]) -> Optional[bytes]:
        """type of GIF"""

    @overload
    async def download_ugoira(self, *, type: Literal["mp4"]) -> Optional[bytes]:
        """type of mp4"""

    async def download_ugoira(
        self, *, type: UGOIRA_RESULT_TYPE = "zip"
    ) -> Union[bytes, list[bytes], None]:
        if self.type != IllustType.ugoira:
            raise ArtWorkTypeError(
                "If you want to download a normal image, "
                'please use this method: "download"'
            )
        metadata = await self.ugoira_metadata()
        data = await self._pixiv_client.download(metadata.zip_url.link)
        if data is None:
            return None
        if type == "zip":
            return data

        zip_file = ZipFile(BytesIO(data))

        if type == "all":
            frames = []
            for frame in metadata.frames:
                with zip_file.open(frame.file) as f:
                    frames.append(f.read())
            return frames

        async with TemporaryDirectory() as directory:
            directory = Path(directory).resolve()
            connect_config_file_path = directory / "list.txt"
            async with async_open(connect_config_file_path, mode="w") as list_file:
                for frame in metadata.frames:
                    with zip_file.open(frame.file) as frame_zip_file:
                        frame_file_path = directory / frame.file
                        async with async_open(frame_file_path, mode="wb") as frame_file:
                            await frame_file.write(frame_zip_file.read())
                    await list_file.write(
                        f"file {frame_file_path.resolve()}\n".replace("\\", "/")
                    )
                    await list_file.write(f"duration {frame.delay / 1000}\n")
            del zip_file
            event = Event()
            if type == "mp4":
                output_path = directory / "out.mp4"
                ffmpeg = (
                    FFmpeg()
                    .option("y")
                    .option("f", "lavfi")
                    .option("i", "anullsrc")
                    .option("f", "concat")
                    .option("safe", 0)
                    .option(
                        "filter_complex",
                        "colormatrix=bt470bg:bt709[0];"
                        "[0]crop='iw-mod(iw,2)':'ih-mod(ih,2)'[main];"
                        "[main]split[v1][v2];"
                        "[v1]palettegen[pal];"
                        "[v2][pal]paletteuse=dither=sierra2_4a",
                    )
                    .option("i", str(connect_config_file_path.resolve()))
                    .option("pix_fmt", "yuv420p10le")
                    .option("c:v", "libx265")
                    .option("c:a", "aac")
                    .option("crf", 0)
                    .option("x265-params", "profile=main10")
                    .option("shortest")
                    .output(str(output_path))
                )
            else:
                output_path = directory / "out.gif"
                ffmpeg = (
                    FFmpeg()
                    .option("y")
                    .option("f", "concat")
                    .option("safe", 0)
                    .option("i", str(connect_config_file_path.resolve()))
                    .option(
                        "filter_complex",
                        "colormatrix=bt470bg:bt709[main];"
                        "[main]split[v1][v2];"
                        "[v1]palettegen[pal];"
                        "[v2][pal]paletteuse=dither=sierra2_4a",
                    )
                    .option("crf", 0)
                    .output(str(output_path))
                )
            ffmpeg.on("completed", lambda: event.set())
            await ffmpeg.execute()
            await event.wait()

            async with async_open(output_path, mode="rb") as file:
                return await file.read()


class Comment(PixivModel):
    id: int
    comment: str
    date: datetime
    user: User
    parent: Annotated[Optional["Comment"], NullDictValidator] = Field(
        None, alias="parent_comment"
    )


class UgoiraMetadata(PixivModel):
    class Frame(PixivModel):
        file: str
        delay: int

    zip_url: ImageUrl = Field(alias="zip_urls")
    frames: list[Frame]
