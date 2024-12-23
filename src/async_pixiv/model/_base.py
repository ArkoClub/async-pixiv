from typing import Any, Optional, Self, TYPE_CHECKING

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    PrivateAttr,
    field_validator,
)

from async_pixiv.utils.context import get_pixiv_client, set_pixiv_client

if TYPE_CHECKING:
    from async_pixiv import PixivClient

__all__ = ("PixivModel", "NullDictValidator")


# noinspection Pydantic
class PixivModel(BaseModel):
    model_config = ConfigDict(validate_default=True, validate_assignment=True)
    _pixiv_client: Optional["PixivClient"] = PrivateAttr(None)

    @classmethod
    def model_validate(cls, *args, **kwargs) -> Self:
        cls.model_rebuild()
        return super().model_validate(*args, **kwargs)

    def __init__(
        self, _pixiv_client: Optional["PixivClient"] = None, **data: Any
    ) -> None:
        pixiv_client = _pixiv_client or get_pixiv_client()
        with set_pixiv_client(pixiv_client):
            super().__init__(**data)
        self._pixiv_client = pixiv_client

    def __str__(self) -> str:
        if hasattr(self, "id"):
            return f'<{self.__class__.__name__} id="{self.id}">'
        else:
            return f"<{self.__class__.__name__}>"

    def __hash__(self) -> int:
        if hasattr(self, "id"):
            return hash((self.__class__.__name__, self.id))
        return super(PixivModel, self).__hash__()

    @field_validator("*", mode="before")
    @classmethod
    def string_validator(cls, value: Any) -> str:
        return None if value == {} or value == "" else value


def _validator[T](value: T) -> T | None:
    if value == {}:
        return None
    else:
        return value


NullDictValidator = BeforeValidator(_validator)
