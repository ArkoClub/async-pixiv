from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from async_pixiv.utils.overwrite import Response


class PixivError(Exception):
    def __init_subclass__(cls, **kwargs) -> None:
        cls.__module__ = "async_pixiv.error"


class LoginError(PixivError):
    pass


class OauthError(PixivError):
    pass


class ArtWorkTypeError(PixivError, TypeError):
    pass


class StatusError(PixivError):
    reason: Optional[str] = None

    def __init__(self, response: "Response") -> None:
        self.response = response

    def __str__(self) -> str:
        return self.reason or self.response


class ApiError(PixivError):
    user_message: Optional[str] = None
    message: Optional[str] = None
    reason: Optional[str] = None
    user_message_details: Optional[str] = None

    def __init__(self, data: dict) -> None:
        self.user_message = data.get("user_message", self.user_message)
        self.message = data.get("message", self.message)
        self.reason = data.get("reason", self.reason)
        self.user_message_details = data.get(
            "user_message_details", self.user_message_details
        )

    def __str__(self) -> str:
        return (
            self.user_message
            or self.message
            or self.reason
            or self.user_message_details
        )


class RateLimit(ApiError):
    reason = "速率限制"


class NotExist(StatusError):
    reason = "作品不存在或无浏览权限"
