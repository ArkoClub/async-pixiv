from pydantic import (
    BaseConfig as PydanticBaseConfig,
    BaseModel as PydanticBaseModel,
)

__all__ = ['PixivModel']


class PixivModel(PydanticBaseModel):
    def __init__(self, **kwargs):
        self.__class__.update_forward_refs()
        super(PixivModel, self).__init__(**kwargs)

    class Config(PydanticBaseConfig):
        try:
            import ujson as json
        except ImportError:
            import json
        json_dumps = json.dumps
        json_loads = json.loads
        validate_all = True
        validate_assignment = True
