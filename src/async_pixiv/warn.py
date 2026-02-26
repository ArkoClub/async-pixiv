__all__ = ("IllustWarning", "PixivWarning")


class PixivWarning(Warning):
    message = ""

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message

    def __init_subclass__(cls, **kwargs) -> None:
        cls.__module__ = "async_pixiv.warn"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PixivWarning):
            return NotImplemented
        return self.message == other.message

    def __hash__(self) -> int:
        return hash((self.__class__.__name__, self.message))


class IllustWarning(PixivWarning):
    """插画相关警告"""
