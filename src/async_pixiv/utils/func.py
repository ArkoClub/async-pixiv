from typing import (
    Callable,
    List,
    TypeVar,
)

from yarl import URL

__all__ = ['proxies_from_env']

T_Wrapped = TypeVar("T_Wrapped", bound=Callable)


# noinspection PyProtectedMember
def proxies_from_env() -> List[URL]:
    from urllib.request import getproxies
    return [
        URL(v)
        for k, v in getproxies().items()
        if k in ("https", "http", "socks4", "socks5", "ws", "wss")
    ]
