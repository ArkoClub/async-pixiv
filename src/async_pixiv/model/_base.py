from pydantic import BaseModel as PydanticBaseModel

__all__ = ['PixivModel']


class PixivModel(PydanticBaseModel):
    def __init__(self, **kwargs):
        self.__class__.update_forward_refs()
        super(PixivModel, self).__init__(**kwargs)
