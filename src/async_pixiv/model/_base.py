from pydantic import (
    BaseConfig as PydanticBaseConfig,
    BaseModel as PydanticBaseModel,
)
# noinspection PyProtectedMember

__all__ = ['PixivModel', 'PixivModelConfig']


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
