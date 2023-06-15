from typing import Literal, TYPE_CHECKING, Union

__all__ = ("StrPath", "UGOIRA_RESULT_TYPE")

if TYPE_CHECKING:
    from os import PathLike
    from pathlib import Path

    StrPath = Union[str, PathLike[str], Path]
else:
    StrPath = Union[str, "PathLike[str]", "Path"]

UGOIRA_RESULT_TYPE = Literal["zip", "jpg", "iter", "gif", "mp4"]
