import datetime
from enum import Enum as BaseEnum
from functools import lru_cache
from typing import (
    TYPE_CHECKING,
    Annotated,
    Awaitable,
    Callable,
    Literal,
    TypeVar,
    Union,
)

import tzlocal
from pydantic import AfterValidator, GetJsonSchemaHandler, ValidationInfo
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from yarl import URL as _URL

__all__ = (
    "UGOIRA_RESULT_TYPE",
    "Datetime",
    "DurationTypes",
    "Enum",
    "EnumType",
    "FilterTypes",
    "IllustTypes",
    "ProgressHandler",
    "ShortTypes",
    "StrPath",
    "TargetTypes",
    "UrlType",
)

if TYPE_CHECKING:
    from os import PathLike
    from pathlib import Path

    from async_pixiv.model.illust import IllustType
    from async_pixiv.model.other.enums import (
        SearchDuration,
        SearchFilter,
        SearchShort,
        SearchTarget,
    )

    StrPath = str | PathLike[str] | Path
    ShortTypes = (
        Literal["date_desc", "date_asc", "popular_desc", "popular_asc"] | SearchShort
    )
    TargetTypes = (
        SearchTarget
        | Literal["partial_match_for_tags", "keyword", "exact_match_for_tags", "text"]
    )
    FilterTypes = Literal["for_android", "for_ios"] | SearchFilter
    DurationTypes = (
        Literal[
            "within_last_day",
            "within_last_week",
            "within_last_month",
            "within_last_year",
        ]
        | SearchDuration
    )
    IllustTypes = Literal["illust", "manga", "novel", "ugoira"] | IllustType
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

ProgressHandler = Callable[[int, int], None | Awaitable[None]]
"""async/sync progress_handler(uploaded_bytes, total_bytes) -> None"""

UGOIRA_RESULT_TYPE = Literal["zip", "jpg", "iter", "gif", "mp4"]

NotImplementedType = type(NotImplemented)


class Enum(BaseEnum):
    def __str__(self) -> str:
        # noinspection PyTypeChecker
        return self.value


EnumType = TypeVar("EnumType", bound=Enum | BaseEnum)


def _datetime_validator(
    value: datetime.datetime,
    info: ValidationInfo,
) -> datetime.datetime:
    timezone = None
    if isinstance(info.context, dict):
        timezone = info.context.get("timezone")

    if timezone is None:
        timezone = tzlocal.get_localzone()
    return value.astimezone(timezone)


Datetime = Annotated[datetime.datetime, AfterValidator(_datetime_validator)]


@lru_cache(128)
def _url_validator(value) -> _URL:
    if isinstance(value, _URL):
        return value
    else:
        return _URL(str(value))


if TYPE_CHECKING:
    UrlType = _URL
else:

    class UrlType:
        def __new__(cls, value) -> _URL:
            return _url_validator(value)

        @classmethod
        def __get_pydantic_core_schema__(cls, _source_type, _handler):
            return core_schema.no_info_plain_validator_function(_url_validator)

        @classmethod
        def __get_pydantic_json_schema__(
            cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            return handler(core_schema.str_schema())
