from async_pixiv.typedefs import Enum
import enum

__all__ = (
    "Quality",
    "SearchTarget",
    "SearchShort",
    "SearchDuration",
    "SearchFilter",
    "SearchAIType",
)


class Quality(Enum):
    Square = "square"
    Medium = "medium"
    Large = "large"
    Original = "original"
    AdaptiveBest = enum.auto()
    """自适应最佳质量"""
    AdaptiveWorst = enum.auto()
    """自适应最差质量"""


class SearchTarget(Enum):
    TAGS_PARTIAL = "partial_match_for_tags"
    """标签部分一致"""

    TAGS_EXACT = "exact_match_for_tags"
    """标签完全一致"""

    TITLE_AND_CAPTION = "title_and_caption"
    """标题、说明文字"""

    text = "text"
    """正文"""

    keyword = "keyword"
    """关键词"""


class SearchShort(Enum):
    DateDecrease = "date_desc"
    DateIncrements = "date_asc"
    PopularDecrease = "popular_desc"
    PopularIncrements = "popular_asc"


class SearchDuration(Enum):
    day = "within_last_day"
    """一天内"""

    week = "within_last_week"
    """一周内"""

    month = "within_last_month"
    """一月内"""

    year = "within_last_year"
    """一年内"""


class SearchFilter(Enum):
    ANDROID = "for_android"
    IOS = "for_ios"


class SearchAIType(Enum):
    disallow = 0
    """过滤AI生成作品"""

    allow = 1
    """显示AI生成作品"""
