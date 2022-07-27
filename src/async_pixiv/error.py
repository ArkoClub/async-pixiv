class PixivError(Exception):
    pass


class LoginError(PixivError):
    pass


class OauthError(PixivError):
    pass
