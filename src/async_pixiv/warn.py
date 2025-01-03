__all__ = ("PixivWarning", "IllustWarning")


class PixivWarning(Warning):
    message = ""

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message

    def __init_subclass__(cls, **kwargs) -> None:
        cls.__module__ = "async_pixiv.warn"

    def __eq__(self, other: Exception) -> bool:
        return self == other


class IllustWarning(PixivWarning):
    """插画相关警告"""
