from typing import List

from yarl import URL


# noinspection PyProtectedMember
def proxies_from_env() -> List[URL]:
    from urllib.request import getproxies
    return [
        URL(v)
        for k, v in getproxies().items()
        if k in ("https", "http", "socks4", "socks5", "ws", "wss")
    ]


def main():
    print(proxies_from_env())


if __name__ == '__main__':
    main()
