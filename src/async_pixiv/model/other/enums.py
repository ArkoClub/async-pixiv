from async_pixiv.typedefs import Enum
import enum

__all__ = (
    "Quality",
    "SearchTarget",
    "SearchShort",
    "SearchDuration",
    "SearchFilter",
)

class  Quality(Enum):
    Square = enum.auto()
    Medium = enum.auto()
    Large = enum.auto()
    Original = enum.auto()

class SearchTarget(Enum):
    TAGS_PARTIAL = "partial_match_for_tags"  # 标签部分一致
    TAGS_EXACT = "exact_match_for_tags"  # 标签完全一致
    TITLE_AND_CAPTION = "title_and_caption"
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
    ANDROID = "for_android"
    IOS = "for_ios"
