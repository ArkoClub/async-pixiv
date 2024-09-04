from async_pixiv.model._base import PixivModel

__all__ = ("Tag", "TagTranslation")


class Tag(PixivModel):
    name: str
    translated_name: str | None = None
    added_by_uploaded_user: bool | None = None

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return self.name


class TagTranslation(PixivModel, extra="allow"):
    zh: str | None = None
    en: str | None = None
    jp: str | None = None
