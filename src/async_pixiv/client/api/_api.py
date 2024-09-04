from async_pixiv.typedefs import Enum

__all__ = ("PixivAPIType",)


class PixivAPIType(Enum):
    APP = "app"
    WEB = "web"
    MIX = "mix"
