from typing import (
    Callable,
    List,
    TypeVar,
)

from yarl import URL

from async_pixiv.error import ApiError, RateLimit

__all__ = ['proxies_from_env', 'raise_for_result']

T_Wrapped = TypeVar("T_Wrapped", bound=Callable)


# noinspection PyProtectedMember
def proxies_from_env() -> List[URL]:
    from urllib.request import getproxies
    return [
        URL(v)
        for k, v in getproxies().items()
        if k in ("https", "http", "socks4", "socks5", "ws", "wss")
    ]


def raise_for_result(data: dict) -> None:
    if data.get('error') is not None:
        error = data['error']
        if error['reason'] == 'Rate Limit':
            raise RateLimit(data)
        else:
            raise ApiError(data)
