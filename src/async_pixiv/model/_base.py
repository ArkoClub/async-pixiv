from typing import TYPE_CHECKING, Any, Self
from weakref import ReferenceType, ref

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    PrivateAttr,
    field_validator,
)

from async_pixiv.error import ClientNotFindError

if TYPE_CHECKING:
    from async_pixiv import PixivClient

__all__ = ("NullDictValidator", "PixivModel")


# noinspection Pydantic
class PixivModel(BaseModel):
    model_config = ConfigDict(validate_default=True, validate_assignment=True)
    _pixiv_client_ref: ReferenceType["PixivClient"] | None = PrivateAttr(None)

    @classmethod
    def model_validate(
        cls, *args, _pixiv_client: "PixivClient" | None = None, **kwargs
    ) -> Self:
        cls.model_rebuild()
        context = kwargs.pop("context", None)
        if _pixiv_client is not None:
            if context is None:
                context = {"timezone": _pixiv_client.timezone}
            elif isinstance(context, dict):
                context = dict(context)
                context.setdefault("timezone", _pixiv_client.timezone)

        if context is not None:
            kwargs["context"] = context

        model: Self = super().model_validate(*args, **kwargs)
        if _pixiv_client is not None:
            model._bind_client(_pixiv_client)
        return model

    def _bind_client(
        self,
        client: "PixivClient",
        _visited: set[int] | None = None,
    ) -> None:
        if _visited is None:
            _visited = set()

        if id(self) in _visited:
            return
        _visited.add(id(self))

        self._pixiv_client_ref = ref(client)
        for field_name in self.__class__.model_fields:
            value = getattr(self, field_name)
            self._bind_client_value(value, client, _visited)

    @classmethod
    def _bind_client_value(
        cls,
        value: Any,
        client: "PixivClient",
        visited: set[int],
    ) -> None:
        if isinstance(value, PixivModel):
            value._bind_client(client, visited)
            return

        if isinstance(value, dict):
            for item in value.values():
                cls._bind_client_value(item, client, visited)
            return

        if isinstance(value, list | tuple | set | frozenset):
            for item in value:
                cls._bind_client_value(item, client, visited)

    @property
    def _pixiv_client(self) -> "PixivClient" | None:
        if self._pixiv_client_ref is not None:
            client = self._pixiv_client_ref()
            if client is not None:
                return client
        return None

    def _require_client(self) -> "PixivClient":
        client = self._pixiv_client
        if client is not None:
            return client

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
