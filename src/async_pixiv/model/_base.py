from typing import Any, Optional, TYPE_CHECKING, TypeVar

from pydantic import (
    BaseModel as PydanticBaseModel,
    ConfigDict,
    PrivateAttr,
)
from pydantic.functional_validators import BeforeValidator

from async_pixiv.utils.context import get_pixiv_client

if TYPE_CHECKING:
    from async_pixiv.client import PixivClient

    Model = TypeVar("Model", bound="BaseModel")

__all__ = ["PixivModel", "PixivModelConfig", "NullDictValidator"]

T = TypeVar("T")


PixivModelConfig = ConfigDict(validate_default=True, validate_assignment=True)


class PixivModel(PydanticBaseModel):
    model_config = PixivModelConfig

    _pixiv_client: Optional["PixivClient"] = PrivateAttr(None)

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._pixiv_client = get_pixiv_client()

    def __new__(cls, *args, **kwargs):
        cls.model_rebuild()
        return super(PixivModel, cls).__new__(cls)

    def __str__(self) -> str:
        if hasattr(self, "id"):
            return f'<{self.__class__.__name__} id="{self.id}">'
        else:
            return f"<{self.__class__.__name__}>"

    def __hash__(self) -> int:
        if hasattr(self, "id"):
            return hash((self.__class__.__name__, self.id))
        return super(PixivModel, self).__hash__()


def _validator(value: T) -> T | None:
    if value == {}:
        return None
    else:
        return value


NullDictValidator = BeforeValidator(_validator)
