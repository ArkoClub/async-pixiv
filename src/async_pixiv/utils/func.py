from typing import (
    Callable,
    TypeVar,
)

from yarl import URL

__all__ = ("oauth_pkce", "proxies_from_env")

T_Wrapped = TypeVar("T_Wrapped", bound=Callable)


# noinspection PyProtectedMember
def proxies_from_env() -> list[URL]:
    from urllib.request import getproxies

    return [
        URL(v)
        for k, v in getproxies().items()
        if k in ("https", "http", "socks4", "socks5", "ws", "wss")
    ]


def oauth_pkce() -> tuple[str, str]:
    from base64 import urlsafe_b64encode
    from hashlib import sha256
    from secrets import token_urlsafe

    verifier = token_urlsafe(32)
    challenge = (
        urlsafe_b64encode(sha256(verifier.encode("ascii")).digest())
        .rstrip(b"=")
        .decode("ascii")
    )
    return verifier, challenge
