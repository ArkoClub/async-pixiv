from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from async_pixiv.client import PixivClient

__all__ = (
    "no_warning",
    "do_nothing",
    "async_do_nothing",
    "PixivClientContext",
    "set_pixiv_client",
    "get_pixiv_client",
)

PixivClientContext: ContextVar["PixivClient"] = ContextVar("PixivClientContext")


@contextmanager
def do_nothing() -> None:
    try:
        yield
    finally:
        ...


@asynccontextmanager
def async_do_nothing() -> None:
    try:
        yield
    finally:
        ...


@contextmanager
def no_warning() -> None:
    import warnings
    from copy import deepcopy

    filters = deepcopy(warnings.filters)
    try:
        warnings.filterwarnings("ignore")
        yield
    finally:
        warnings.resetwarnings()
        for f in filters:
            # noinspection PyUnresolvedReferences
            warnings.filters.append(f)


@contextmanager
def set_pixiv_client(client: "PixivClient") -> "PixivClient":
    token = PixivClientContext.set(client)
    try:
        yield client
    finally:
        PixivClientContext.reset(token)


def get_pixiv_client(raise_error: bool = False) -> Optional["PixivClient"]:
    try:
        return PixivClientContext.get()
    except LookupError:
        if not raise_error:
            return None
        else:
            raise LookupError("You should set your Pixiv client first.")
