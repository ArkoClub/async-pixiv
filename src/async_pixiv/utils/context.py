from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Iterator, Optional

if TYPE_CHECKING:
    from pytz.tzinfo import DstTzInfo

    from async_pixiv.client import PixivClient

__all__ = (
    "PixivClientContext",
    "TimezoneContext",
    "async_do_nothing",
    "do_nothing",
    "get_pixiv_client",
    "get_timezone",
    "no_warning",
    "set_pixiv_client",
    "set_timezone",
)

PixivClientContext: ContextVar["PixivClient"] = ContextVar("PixivClientContext")
TimezoneContext: ContextVar["DstTzInfo"] = ContextVar("timezone")


@contextmanager
def do_nothing() -> Iterator[None]:
    try:
        yield
    finally:
        ...


@asynccontextmanager
def async_do_nothing() -> Iterator[None]:
    try:
        yield
    finally:
        ...


@contextmanager
def no_warning() -> Iterator[None]:
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
def set_pixiv_client(client: "PixivClient") -> Iterator["PixivClient"]:
    token = PixivClientContext.set(client)
    try:
        yield client
    finally:
        PixivClientContext.reset(token)


def get_pixiv_client(raise_error: bool = False) -> Optional["PixivClient"]:
    try:
        return PixivClientContext.get()
    except LookupError:
        from async_pixiv.error import ClientNotFindError

        if not raise_error:
            return None
        raise ClientNotFindError() from None


@contextmanager
def set_timezone(timezone: "DstTzInfo") -> Iterator["DstTzInfo"]:
    token = TimezoneContext.set(timezone)
    try:
        yield timezone
    finally:
        TimezoneContext.reset(token)


def get_timezone(raise_error: bool = False) -> Optional["DstTzInfo"]:
    try:
        return TimezoneContext.get()
    except LookupError as e:
        if raise_error:
            raise e
