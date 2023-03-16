from enum import Enum as BaseEnum

__all__ = ("Enum", "SearchTarget", "SearchShort", "SearchDuration", "SearchFilter")


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
    date_desc = "date_desc"
    date_asc = "date_asc"
    popular_desc = "popular_desc"
    popular_asc = "popular_asc"


class SearchDuration(Enum):
    day = "within_last_day"
    week = "within_last_week"
    month = "within_last_month"
    year = "within_last_year"


class SearchFilter(Enum):
    android = "for_android"
    ios = "for_ios"
