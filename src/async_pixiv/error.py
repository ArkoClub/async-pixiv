from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from async_pixiv.utils.overwrite import Response

__all__ = (
    "PixivError",
    "ClientNotFindError",
    "LoginError",
    "OauthError",
    "InvalidRefreshToken",
    "ArtWorkTypeError",
    "StatusError",
    "APIError",
    "RateLimitError",
    "NotExistError",
    "DataValidationError"
)


class PixivError(Exception):
    message: str = ""

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message

    def __init_subclass__(cls, **kwargs) -> None:
        cls.__module__ = "async_pixiv.error"

    def __eq__(self, other: Exception) -> bool:
        return self == other

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.message!r}"


class ClientNotFindError(PixivError):
    message = "Could not find an instantiated client."


class LoginError(PixivError):
    pass


class OauthError(PixivError):
    pass


class InvalidRefreshToken(OauthError):
    message = "错误的 Refresh Token "


class ArtWorkTypeError(PixivError, TypeError):
    pass


class StatusError(PixivError):
    reason: Optional[str] = None

    def __init__(self, response: "Response") -> None:
        self.response = response
        try:
            response_json = response.json()
        except _:  # noqa: F821
            response_json = None

        if response_json is not None:
            self.reason = (
                response_json["error"]["message"]
                or response_json["error"]["reason"]
                or response_json["error"]["user_message"]
            )

    def __str__(self) -> str:
        return self.reason or self.response


class APIError(PixivError):
    user_message: str = ""
    user_message_details: str = ""

    def __init__(self, data: dict) -> None:
        self.user_message = data.get("user_message", self.user_message)
        self.message = data.get("message", self.message)
        self.user_message_details = data.get(
            "user_message_details", self.user_message_details
        )

    def __str__(self) -> str:
        return self.user_message or self.message or self.user_message_details


class RateLimitError(APIError):
    message = "速率限制"


class NotExistError(StatusError):
    message = "作品不存在或无浏览权限"

class DataValidationError(APIError):
    message = "Data validation failed."

    def __init__(self, data: dict):
        self.data = data
