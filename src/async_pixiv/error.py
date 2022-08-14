class PixivError(Exception):
    pass


class LoginError(PixivError):
    pass


class OauthError(PixivError):
    pass


class ArtWorkTypeError(PixivError, TypeError):
    pass
