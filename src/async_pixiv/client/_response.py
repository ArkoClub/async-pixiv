from logging import getLogger
from typing import Any, Self

from httpx import Response as DefaultResponse

from async_pixiv.error import (
    APIError,
    InvalidRefreshToken,
    NotExistError,
    PixivError,
    RateLimitError,
)

try:
    from orjson import loads as default_json_loads
except ImportError:
    from json import loads as default_json_loads


__all__ = ("Response",)


logger = getLogger(__name__)

STATUS_ERROR_MAP = {
    404: NotExistError,
}
RESULT_ERROR_MAP = {
    "Rate Limit": RateLimitError,
    "invalid_grant": InvalidRefreshToken,
}


class Response(DefaultResponse):
    _json_data: dict[str, Any] | None = None

    def __init__(self, *args, json_loads: callable = default_json_loads, **kwargs):
        super().__init__(*args, **kwargs)
        self._json_loads = json_loads

    def raise_for_status(self) -> Self:
        if self.status_code != 200:
            if (error := STATUS_ERROR_MAP.get(self.status_code)) is not None:
                raise error(self)
            else:
                super().raise_for_status()
        return self

    def raise_for_result(self) -> Self:
        if (json_data := self.json()) is not None:
            if (errors := json_data.get("errors")) is not None and errors:
                raise PixivError(errors)
            elif (error := json_data.get("error")) is not None and error:
                raise RESULT_ERROR_MAP.get(error["message"], APIError)(error)
        return self

    def raise_error(self) -> Self:
        if self.content is not None:
            return self.raise_for_result()
        return self.raise_for_status().raise_for_result()

    def json(self, **kwargs: Any) -> dict[str, Any]:
        return self._json_loads(self.content, **kwargs)
