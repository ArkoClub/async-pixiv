from typing import (
    Optional,
    TypeVar,
)

from pydantic import (
    BaseConfig as PydanticBaseConfig,
    BaseModel as PydanticBaseModel,
    validator,
)

__all__ = [
    'PixivModel', 'PixivModelConfig',
    'null_dict_validator'
]

T = TypeVar('T')


class PixivModelConfig(PydanticBaseConfig):
    try:
        import ujson as json
    except ImportError:
        import json
    json_dumps = json.dumps
    json_loads = json.loads
    validate_all = True
    validate_assignment = True


class PixivModel(PydanticBaseModel):
    Config = PixivModelConfig

    def __new__(cls, *args, **kwargs):
        cls.update_forward_refs()
        return super(PixivModel, cls).__new__(cls)

    def __str__(self) -> str:
        if hasattr(self, 'id'):
            return f"<{self.__class__.__name__} id=\"{self.id}\">"
        else:
            return f"<{self.__class__.__name__}>"
    
    def __hash__(self) -> int:
        if hasattr(self, 'id'):
            return hash((self.__class__.__name__, self.id))
        return super(PixivModel, self).__hash__()


def null_dict_validator(*fields: str) -> classmethod:
    def v(cls, value: T) -> Optional[T]:
        if value == {}:
            return None
        else:
            return value

    return validator(*fields, pre=True, always=True, allow_reuse=True)(v)
