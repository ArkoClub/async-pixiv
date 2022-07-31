from typing import Optional

from pydantic import HttpUrl

from async_pixiv.model._base import PixivModel


class ImageUrl(PixivModel):
    square_medium: Optional[HttpUrl]
    medium: Optional[HttpUrl]
    large: Optional[HttpUrl]
    original: Optional[HttpUrl]
