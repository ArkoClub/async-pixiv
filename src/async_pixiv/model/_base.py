from typing import TYPE_CHECKING, Any, Self
from weakref import ReferenceType, ref

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

__all__ = ("NullDictValidator", "PixivModel")


# noinspection Pydantic
class PixivModel(BaseModel):
    model_config = ConfigDict(validate_default=True, validate_assignment=True)
    _pixiv_client_ref: ReferenceType["PixivClient"] | None = PrivateAttr(None)

    @classmethod
    def model_validate(cls, *args, **kwargs) -> Self:
        cls.model_rebuild()
        return super().model_validate(*args, **kwargs)

    def __init__(self, _pixiv_client: "PixivClient" | None = None, **data: Any) -> None:
        pixiv_client = _pixiv_client or get_pixiv_client()
        if pixiv_client is None:
            super().__init__(**data)
            return

        with set_pixiv_client(pixiv_client):
            super().__init__(**data)
        self._pixiv_client_ref = ref(pixiv_client)

    @property
    def _pixiv_client(self) -> "PixivClient" | None:
        if self._pixiv_client_ref is not None:
            client = self._pixiv_client_ref()
            if client is not None:
                return client
        return get_pixiv_client()

    def _require_client(self) -> "PixivClient":
        client = self._pixiv_client
        if client is not None:
            return client

        from async_pixiv.error import ClientNotFindError

        raise ClientNotFindError() from None

    def __str__(self) -> str:
        if hasattr(self, "id"):
            return f'<{self.__class__.__name__} id="{self.id}">'
        else:
            return f"<{self.__class__.__name__}>"

    def __hash__(self) -> int:
        if hasattr(self, "id"):
            return hash((self.__class__.__name__, self.id))
        return super().__hash__()

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
