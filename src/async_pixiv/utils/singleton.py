from typing import TypeVar

__all__ = ("Singleton", "singleton")

T = TypeVar("T")


class Singleton(type):
    _instances: dict[type, object] = {}

    def __call__(cls: T, *args, **kwargs) -> T:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def singleton(_class: type[T]) -> type[T]:
    class Class(_class):
        _instance: T | None = None

        def __new__(cls, *args, **kwargs):
            if Class._instance is None:
                Class._instance = super(Class, cls).__new__(cls, *args, **kwargs)
                Class._instance._sealed = False
            return Class._instance

        def __init__(self, *args, **kwargs):
            if self._sealed:
                return
            super().__init__(*args, **kwargs)
            self._sealed = True

    Class.__name__ = _class.__name__
    return Class
