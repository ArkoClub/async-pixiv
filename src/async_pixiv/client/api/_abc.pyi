from abc import ABC
from threading import RLock as Lock
from typing import Optional, Sequence, TYPE_CHECKING

from async_pixiv.model.other.result import PageResult
from async_pixiv.typedefs import DurationTypes, ShortTypes

if TYPE_CHECKING:
    from async_pixiv.client import PixivClient

__all__ = ("APIBase",)

class APIBase[T](ABC):
    _lock: Lock

    _pixiv_client: "PixivClient"
    _type: str

    @property
    def type(self) -> str:
        pass

    def __init_subclass__(cls, **kwargs) -> None:
        pass

    def __init__(
        self,
        client: Optional["PixivClient"] = None,
    ) -> None:
        pass

    async def __call__(self, id: int) -> T:
        pass

    async def detail(self, id: int) -> T:
        pass

    async def search(
        self,
        words: str | Sequence[str],
        *,
        sort: ShortTypes | None = None,
        duration: DurationTypes | None = None,
        offset: int | None = None,
        **kwargs,
    ) -> PageResult:
        pass

    async def recommended(self) -> PageResult:
        pass
