from multiprocessing import RLock as Lock
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from multiprocessing.synchronize import RLock as LockType

__all__ = ("Singleton", "singleton")

T = TypeVar("T")


class Singleton(type):
    _lock: "LockType" = Lock()
    _instances: dict[type[T], T] = {}

    def __call__(cls: T, *args, **kwargs) -> T:
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def singleton(_class: type[T]) -> type[T]:
    class Class(_class):
        _instance: T | None = None

        def __new__(cls, *args, **kwargs):
            if Class._instance is None:
                Class._instance = super().__new__(cls, *args, **kwargs)
                Class._instance._sealed = False
            return Class._instance

        def __init__(self, *args, **kwargs):
            if self._sealed:
                return
            super().__init__(*args, **kwargs)
            self._sealed = True

    Class.__name__ = _class.__name__
    return Class
