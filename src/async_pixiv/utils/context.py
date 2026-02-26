import warnings
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from copy import deepcopy
from typing import TYPE_CHECKING, Iterator, Optional

if TYPE_CHECKING:
    from pytz.tzinfo import DstTzInfo

__all__ = (
    "TimezoneContext",
    "async_do_nothing",
    "do_nothing",
    "get_timezone",
    "no_warning",
    "set_timezone",
)

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
