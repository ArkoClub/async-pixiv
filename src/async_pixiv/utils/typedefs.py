from os import PathLike
from typing import TYPE_CHECKING, Union

__all__ = ("StrPath",)

if TYPE_CHECKING:
    from pathlib import Path

    StrPath = Union[str, PathLike[str], Path]
else:
    StrPath = Union[str, PathLike[str], "Path"]
