import sys

from yarl import URL

__all__ = (
    "APP_API_HOST",
    "WEB_API_HOST",
    "IS_WINDOWS",
)

APP_API_HOST = URL("https://app-api.pixiv.net/")
WEB_API_HOST = URL("https://www.pixiv.net/ajax/")

IS_WINDOWS = sys.platform == "win32"
