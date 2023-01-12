class PixivError(Exception):
    def __init_subclass__(cls, **kwargs) -> None:
        cls.__module__ = 'async_pixiv.error'


class LoginError(PixivError):
    pass


class OauthError(PixivError):
    pass


class ArtWorkTypeError(PixivError, TypeError):
    pass


class ApiError(PixivError):
    def __init__(self, data: dict) -> None:
        self.user_message = data.get('user_message', None)
        self.message = data.get('message', None)
        self.reason = data.get('reason', None)
        self.user_message_details = data.get('user_message_details')

    def __str__(self) -> str:
        return self.reason


class RateLimit(ApiError):
    pass
