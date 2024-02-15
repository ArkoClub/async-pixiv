import sys

from yarl import URL

__all__ = ("IS_WINDOWS", "AJAX_HOST", "API_HOST", "V1_API", "V2_API")


API_HOST = URL("https://app-api.pixiv.net")
AJAX_HOST = URL("https://www.pixiv.net/ajax")
V1_API = API_HOST / "v1"
V2_API = API_HOST / "v2"

IS_WINDOWS = sys.platform == "win32"
