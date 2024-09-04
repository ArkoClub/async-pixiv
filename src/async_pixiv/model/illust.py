from asyncio import Event
from functools import cached_property
from io import BytesIO
from pathlib import Path
from typing import Any, Literal, overload
from zipfile import ZipFile

from aiofiles.tempfile import TemporaryDirectory
from pydantic import Field
from functools import cache
from aiofiles import open as async_open

from async_pixiv.error import ArtWorkTypeError
from async_pixiv.model._base import PixivModel
from async_pixiv.model.other.enums import Quality
from async_pixiv.model.other.image import ImageUrl
from async_pixiv.model.other.result import UgoiraMetadata
from async_pixiv.model.other.tag import Tag
from async_pixiv.model.user import User
from async_pixiv.typedefs import Datetime, Enum, URL
from async_pixiv.utils.ffmpeg import FFmpeg

UGOIRA_RESULT_TYPE = Literal["zip", "gif", "mp4", "frame"]

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


class IllustMetaSinglePage(PixivModel):
    original: URL | None = Field(None, alias="original_image_url")

    @property
    def link(self) -> URL | None:
        return self.original


class IllustMetaPage(PixivModel):
    image_urls: ImageUrl


class Illust(PixivModel):
    id: int
    title: str
    type: "IllustType"
    image_urls: ImageUrl
    caption: str | None = None
    restrict: int
    user: User
    tags: list[Tag] = []
    tools: list[str]
    create_date: Datetime
    page_count: int
    width: int
    height: int
    sanity_level: int
    x_restrict: int
    meta_single_page: IllustMetaSinglePage | None = None
    meta_pages: list[IllustMetaPage]
    total_view: int
    total_bookmarks: int
    is_bookmarked: bool
    visible: bool
    is_muted: bool
    ai_type: int = Field(alias="illust_ai_type")
    illust_book_style: int

    comment_access_control: int | None = None
    total_comments: int | None = None

    @cached_property
    def link(self) -> URL:
        return URL(f"https://www.pixiv.net/artworks/{self.id}")

    @cache
    async def get_ugoira_metadata(self) -> UgoiraMetadata:
        return (await self._pixiv_client.ILLUST.ugoira_metadata(self.id)).metadata

    @overload
    async def download_ugoira(self, quality: Quality = Quality.Original,*, result_type: Literal["zip"] = "zip") -> bytes | None:
        """type of zip"""

    @overload
    async def download_ugoira(self, quality: Quality = Quality.Original,*, result_type: Literal["frame"] = "frame") -> list[bytes] | None:
        """type of frame"""

    @overload
    async def download_ugoira(self, quality: Quality = Quality.Original,*, result_type: Literal["gif"] = "gif") -> bytes | None:
        """type of GIF"""

    @overload
    async def download_ugoira(self, quality: Quality = Quality.Original,*, result_type: Literal["mp4"] = "mp4") -> bytes | None:
        """type of mp4"""

    async def download_ugoira(
        self, quality: Quality = Quality.Original,*, result_type: UGOIRA_RESULT_TYPE = "zip"
    ) -> bytes | list[bytes] | None:
        if self.type != IllustType.ugoira:
            raise ArtWorkTypeError(
                "If you want to download a normal image, "
                'please use this method: "download"'
            )

        metadata = await self.get_ugoira_metadata()

        match quality:
            case Quality.Large:
                link = metadata.zip_url.large or metadata.zip_url.medium or metadata.zip_url.square
            case Quality.Medium:
                link = metadata.zip_url.medium or metadata.zip_url.square
            case Quality.Square:
                link = metadata.zip_url.square
            case _:
                link = metadata.zip_url.link
        link = metadata.zip_url.link if link is None else link

        data = await self._pixiv_client.download(link)
        if data is None:
            return None
        if result_type == "zip":
            return data

        zip_file = ZipFile(BytesIO(data))

        if result_type == "frame":
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
            if result_type == "mp4":
                output_path = directory / "out.mp4"
                # noinspection SpellCheckingInspection
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
            else: # gif
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