import inspect
from typing import Callable, ParamSpec

from async_pixiv.utils.context import get_pixiv_client

__all__ = ("auto_client",)


P = ParamSpec("P")


def auto_client[R](func: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        signature = inspect.signature(func)
        for name, param in signature.parameters.items():
            if (
                param.name == "client"
                and any(
                    [
                        isinstance(param.annotation, str)
                        and param.annotation == "PixivClient",
                        isinstance(param.annotation, type)
                        and param.annotation.__name__ == "PixivClient",
                    ]
                )
                and kwargs.get("client") is None
            ):
                kwargs["client"] = get_pixiv_client()

        return func(*args, **kwargs)

    return wrapper
