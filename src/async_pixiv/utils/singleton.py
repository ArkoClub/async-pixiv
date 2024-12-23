from multiprocessing import RLock as Lock
from typing import Dict, Optional, TYPE_CHECKING, Type, TypeVar

if TYPE_CHECKING:
    from multiprocessing.synchronize import RLock as LockType

__all__ = ("Singleton", "singleton")

T = TypeVar('T')


class Singleton(type):
    _lock: "LockType" = Lock()
    _instances: Dict[Type[T], T] = {}

    def __call__(cls: T, *args, **kwargs) -> T:
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def singleton(_class: Type[T]) -> Type[T]:
    class Class(_class):
        _instance: Optional[T] = None

        def __new__(cls, *args, **kwargs):
            if Class._instance is None:
                Class._instance = super(
                    Class,
                    cls
                ).__new__(
                    cls,
                    *args,
                    **kwargs
                )
                Class._instance._sealed = False
            return Class._instance

        def __init__(self, *args, **kwargs):
            if self._sealed:
                return
            super(Class, self).__init__(*args, **kwargs)
            self._sealed = True

    Class.__name__ = _class.__name__
    return Class
