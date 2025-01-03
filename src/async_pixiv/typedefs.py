from datetime import datetime
from enum import Enum as BaseEnum
from functools import cached_property, lru_cache
from typing import (
    TYPE_CHECKING,
    Annotated,
    Awaitable,
    Callable,
    Literal,
    NoReturn,
    Optional,
    Protocol,
    Self,
    TypeVar,
    Union,
)

import tzlocal
from pydantic import AfterValidator, PlainValidator
from yarl import URL as _URL

from async_pixiv.utils.context import get_timezone
from async_pixiv.utils.magic import curses

__all__ = (
    "ShortTypes",
    "TargetTypes",
    "FilterTypes",
    "DurationTypes",
    "IllustTypes",
    "StrPath",
    "UGOIRA_RESULT_TYPE",
    "UrlType",
    "Enum",
    "EnumType",
    "Datetime",
    "ProgressHandler",
)

if TYPE_CHECKING:
    from io import BytesIO
    from os import PathLike
    from pathlib import Path

    from multidict import MultiDictProxy

    from async_pixiv import PixivClient
    from async_pixiv.model.illust import IllustType
    from async_pixiv.model.other.enums import (
        SearchDuration,
        SearchFilter,
        SearchShort,
        SearchTarget,
    )

    StrPath = Union[str, PathLike[str], Path]
    ShortTypes = Union[
        Literal["date_desc", "date_asc", "popular_desc", "popular_asc"], SearchShort
    ]
    TargetTypes = Union[
        SearchTarget,
        Literal["partial_match_for_tags", "keyword", "exact_match_for_tags", "text"],
    ]
    FilterTypes = Union[Literal["for_android", "for_ios"], SearchFilter]
    DurationTypes = Union[
        Literal[
            "within_last_day",
            "within_last_week",
            "within_last_month",
            "within_last_year",
        ],
        SearchDuration,
    ]
    IllustTypes = Union[Literal["illust", "manga", "novel", "ugoira"], IllustType]
else:
    StrPath = Union[str, "PathLike[str]", "Path"]

    TargetTypes = Union[
        "SearchTarget",
        Literal["partial_match_for_tags", "keyword", "exact_match_for_tags", "text"],
    ]
    ShortTypes = Union[
        Literal["date_desc", "date_asc", "popular_desc", "popular_asc"], "SearchShort"
    ]
    FilterTypes = Union[Literal["for_android", "for_ios"], "SearchFilter"]

    DurationTypes = Union[
        Literal[
            "within_last_day",
            "within_last_week",
            "within_last_month",
            "within_last_year",
        ],
        "SearchDuration",
    ]

    IllustTypes = Union[Literal["illust", "manga", "novel", "ugoira"], "IllustType"]

ProgressHandler = Callable[[int, int], Union[NoReturn, Awaitable[NoReturn]]]
"""async/sync progress_handler(uploaded_bytes, total_bytes) -> Noreturn"""

UGOIRA_RESULT_TYPE = Literal["zip", "jpg", "iter", "gif", "mp4"]

NotImplementedType = type(NotImplemented)


class Enum(BaseEnum):
    def __str__(self) -> str:
        # noinspection PyTypeChecker
        return self.value


EnumType = TypeVar("EnumType", bound=Union[Enum, BaseEnum])


def _datetime_validator(value: datetime) -> datetime:
    return value.astimezone(get_timezone() or tzlocal.get_localzone())


Datetime = Annotated[datetime, AfterValidator(_datetime_validator)]


@curses(_URL)
async def download(
    self: _URL,
    method: Literal["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"] = "GET",
    *,
    output: Union[StrPath, "BytesIO", None] = None,
    chunk_size: int | None = None,
    progress_handler: ProgressHandler | None = None,
    client: Optional["PixivClient"] = None,
) -> bytes:
    if client is None:
        from async_pixiv.utils.context import get_pixiv_client

        client = get_pixiv_client()
    return await client.download(
        self,
        method,
        output=output,
        chunk_size=chunk_size,
        progress_handler=progress_handler,
    )


# noinspection PyPropertyDefinition
class URL_Protocol(Protocol):  # NOSONAR
    @classmethod
    def build(
        cls,
        *,
        scheme="",
        authority="",
        user=None,
        password=None,
        host="",
        port=None,
        path="",
        query=None,
        query_string="",
        fragment="",
        encoded=False,
    ) -> str | Self: ...

    async def download(
        self,
        method: Literal["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"] = "GET",
        *,
        output: Union[StrPath, "BytesIO"] | None = None,
        chunk_size: int | None = None,
        progress_handler: ProgressHandler | None = None,
        client: Optional["PixivClient"] = None,
    ) -> Union["Path", bytes, "BytesIO"]: ...

    def __str__(self) -> bytes: ...
    def __repr__(self) -> str: ...
    def __bytes__(self) -> bytes: ...
    def __hash__(self) -> int: ...
    def __eq__(self, other) -> bool | NotImplementedType: ...
    def __le__(self, other) -> bool | NotImplementedType: ...
    def __lt__(self, other) -> bool | NotImplementedType: ...
    def __ge__(self, other) -> bool | NotImplementedType: ...
    def __gt__(self, other) -> bool | NotImplementedType: ...
    def __truediv__(self, name) -> NotImplementedType | None: ...
    def __mod__(self, query): ...
    def __bool__(self) -> bool: ...
    def __getstate__(self) -> str | NotImplementedType: ...
    def __setstate__(self, state): ...
    def is_absolute(self) -> bool: ...
    def is_default_port(self) -> bool: ...
    def origin(self) -> Self: ...
    def relative(self) -> Self: ...

    @property
    def scheme(self) -> str: ...
    @property
    def raw_authority(self) -> str: ...

    @cached_property
    def authority(self) -> str: ...

    @property
    def raw_user(self) -> str | None: ...

    @cached_property
    def user(self) -> str | None | type[str]: ...

    @property
    def raw_password(self) -> str | None: ...

    @cached_property
    def password(self) -> str | None | type[str]: ...

    @property
    def raw_host(self) -> str | None: ...

    @cached_property
    def host(self) -> str | None: ...

    @property
    def port(self) -> int | None: ...

    @property
    def explicit_port(self) -> int | None: ...

    @property
    def raw_path(self) -> str: ...

    @cached_property
    def path(self) -> str | None | type[str]: ...

    @cached_property
    def query(self) -> "MultiDictProxy[str]": ...

    @property
    def raw_query_string(self) -> str: ...

    @cached_property
    def query_string(self) -> str | None | type[str]: ...

    @cached_property
    def path_qs(self) -> str | None | type[str]: ...

    @cached_property
    def raw_path_qs(self) -> str: ...

    @property
    def raw_fragment(self) -> str: ...

    @cached_property
    def fragment(self) -> str | None | type[str]: ...

    @cached_property
    def raw_parts(self) -> tuple[str]: ...

    @cached_property
    def parts(self) -> tuple[str | None | type[str]]: ...

    @cached_property
    def parent(self) -> Self: ...

    @cached_property
    def raw_name(self) -> str: ...

    @cached_property
    def name(self) -> str | None | type[str]: ...

    @cached_property
    def raw_suffix(self) -> str: ...

    @cached_property
    def suffix(self) -> str | None | type[str]: ...

    @cached_property
    def raw_suffixes(self) -> tuple | tuple[str]: ...

    @cached_property
    def suffixes(self) -> tuple[str | None | type[str]]: ...


@lru_cache(128)
def _url_validator(value) -> _URL:
    if isinstance(value, _URL):
        return value
    else:
        return _URL(str(value))


UrlType = Annotated[URL_Protocol, PlainValidator(_url_validator)]
