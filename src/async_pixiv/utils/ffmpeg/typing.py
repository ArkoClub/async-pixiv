from numbers import Number
from typing import Iterable, Union

__all__ = ("OptionItem", "Option")

OptionItem = Union[str, Number]
Option = Union[OptionItem, Iterable[OptionItem]]
