from enum import Enum as BaseEnum

from typing import TypeVar, Union

__all__ = (
    "Enum",
    "EnumType",
    "SearchTarget",
    "SearchShort",
    "SearchDuration",
    "SearchFilter",
)


class Enum(BaseEnum):
    def __str__(self) -> str:
        # noinspection PyTypeChecker
        return self.value


class SearchTarget(Enum):
    partial = "partial_match_for_tags"  # 标签部分一致
    full = "exact_match_for_tags"  # 标签完全一致
    text = "text"  # 正文
    keyword = "keyword"  # 关键词


class SearchShort(Enum):
    DateDecrease = "date_desc"
    DateIncrements = "date_asc"
    PopularDecrease = "popular_desc"
    PopularIncrements = "popular_asc"


class SearchDuration(Enum):
    day = "within_last_day"
    week = "within_last_week"
    month = "within_last_month"
    year = "within_last_year"


class SearchFilter(Enum):
    android = "for_android"
    ios = "for_ios"


EnumType = TypeVar("EnumType", bound=Union[Enum, BaseEnum])
