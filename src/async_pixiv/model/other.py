from enum import IntEnum
from typing import Optional

from pydantic import HttpUrl

from async_pixiv.model._base import PixivModel

__all__ = [
    'Series',
    'ImageUrl',
    'Tag', 'TagTranslation',
    'AIType'
]


class Series(PixivModel):
    id: int
    title: str


class ImageUrl(PixivModel):
    square_medium: Optional[HttpUrl]
    medium: Optional[HttpUrl]
    large: Optional[HttpUrl]
    original: Optional[HttpUrl]


class TagTranslation(PixivModel):
    zh: Optional[str]
    en: Optional[str]
    jp: Optional[str]


class Tag(PixivModel):
    name: str
    translated_name: Optional[str]
    added_by_uploaded_user: Optional[bool]


class AIType(IntEnum):
    NONE = 0
    """没有使用AI"""

    HALF = 1
    """使用了AI进行辅助"""

    FULL = 2
    """使用AI生成"""
