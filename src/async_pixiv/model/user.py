import enum
from datetime import date
from functools import cached_property
from typing import Annotated

import annotated_types
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from async_pixiv.model._base import PixivModel
from async_pixiv.model.other.image import AccountImage, ImageUrl
from async_pixiv.typedefs import Enum, UrlType

__all__ = (
    "User",
    "Account",
    "UserGender",
    "UserProfile",
    "UserTwitter",
    "UserJob",
    "UserJobType",
    "UserArtCount",
    "FullUser",
    "UserProfilePublicity",
    "UserWorkspace",
    "UserBirthday",
)


class User(PixivModel):
    id: int
    """用户UID"""

    name: str
    """用户昵称"""

    account: str
    """用户账户ID"""
    profile_image: ImageUrl = Field(alias="profile_image_urls")
    is_followed: bool | None = None
    is_access_blocking_user: bool | None = None

    @cached_property
    def link(self) -> UrlType:
        return UrlType(f"https://www.pixiv.net/users/{self.id}")

    async def detail(self) -> "FullUser":
        if self._pixiv_client is None:
            from async_pixiv.error import ClientNotFindError

            raise ClientNotFindError()
        return await self._pixiv_client.USER.detail(self.id)


class Account(User):
    profile_image: AccountImage = Field(alias="profile_image_urls")
    mail_address: EmailStr | None = None
    is_premium: bool
    x_restrict: int
    is_mail_authorized: bool
    require_policy_agreement: bool


class UserGender(Enum):
    Female = "female"
    Male = "male"
    Unknown = "unknown"


class UserBirthday(BaseModel):
    year: (
        Annotated[int, annotated_types.Gt(0), annotated_types.Le(date.today().year + 1)]
        | None
    ) = None
    month: Annotated[int, annotated_types.Ge(1), annotated_types.Le(12)] | None = None
    day: Annotated[int, annotated_types.Ge(1), annotated_types.Le(31)] | None = None

    def __init__(
        self,
        year: str | int | None = None,
        month: str | int | None = None,
        day: str | int | None = None,
    ) -> None:
        super().__init__(year=year, month=month, day=day)

    def __repr__(self) -> str:
        return f"<UserBirthday {self.__str__()}>"

    def __str__(self) -> str:
        return (
            "" if self.year is None else f"{self.year}-"
        ) + f"{self.month}-{self.day}"

    def date(self) -> date:
        return date(year=self.year or date.today().year, month=self.month, day=self.day)


class UserJobType(Enum):
    IT = enum.auto()
    OfficeWorker = enum.auto()
    Engineer = enum.auto()
    Business = enum.auto()
    Creator = enum.auto()
    Sales = enum.auto()
    Service = enum.auto()
    Construction = enum.auto()
    Management = enum.auto()
    Specialist = enum.auto()
    PublicServant = enum.auto()
    Teacher = enum.auto()
    SelfEmployed = enum.auto()
    Artist = enum.auto()
    Freeter = enum.auto()
    ElementarySchoolStudent = enum.auto()
    MiddleSchoolStudent = enum.auto()
    HighSchoolStudent = enum.auto()
    UniversityStudent = enum.auto()
    VocationalSchoolStudent = enum.auto()
    StayAtHomeParent = enum.auto()
    SeekingEmployment = enum.auto()
    Other = enum.auto()

    def __str__(self) -> str:
        return self.name


class UserJob(BaseModel):
    job_type: UserJobType
    job_type_name: str


class UserArtCount(BaseModel):
    illust: int
    manga: int
    novel: int

    illust_series: int
    novel_series: int


class UserTwitter(PixivModel):
    account: str | None = None

    @property
    def url(self) -> UrlType:
        return UrlType(f"https://twitter.com/{self.account}")

    def __str__(self) -> str:
        return f"@{self.account}"

    def __repr__(self) -> str:
        return f"<Twitter @{self.account}>"


class UserProfile(PixivModel):
    webpage: UrlType | None = None
    gender: UserGender = Field(alias="gender")
    birthday: UserBirthday
    region: str | None = None
    address_id: int
    country_code: str | None = None
    job: UserJob | None = None
    followers: int = Field(alias="total_follow_users")
    """关注数"""

    connections: int = Field(alias="total_mypixiv_users")
    """好P友"""

    art_count: UserArtCount

    bookmarks: int = Field(alias="total_illust_bookmarks_public")
    background_image: UrlType | None = Field(None, alias="background_image_url")

    twitter: UserTwitter | None = None
    pawoo_url: UrlType | None = None

    is_premium: bool
    is_using_custom_profile_image: bool

    @model_validator(mode="before")
    @classmethod
    def birthday_validate(cls, data: dict) -> dict:
        keys = ["birth", "birth_day", "birth_year"]
        birth, birth_day, birth_year = tuple(map(lambda x: data.pop(x, None), keys))
        year, month, day = None, None, None
        if birth:
            year, month, day = tuple(map(int, birth.split("-")))
        elif birth_day:
            month, day = tuple(map(int, birth_day.split("-")))
        elif birth_year:
            year = birth_year
        data["birthday"] = UserBirthday(year, month, day)
        return data

    @model_validator(mode="before")
    @classmethod
    def job_validate(cls, data: dict) -> dict:
        keys = ["job", "job_id"]
        job, job_type_id = tuple(map(lambda x: data.pop(x, None), keys))
        if job == "" or job is None:
            data["job"] = None
            return data
        job_type = UserJobType(job_type_id)
        data["job"] = UserJob(job_type=job_type, job_type_name=job)
        return data

    @model_validator(mode="before")
    @classmethod
    def art_count_validate(cls, data: dict) -> dict:
        keys = [
            "total_illusts",
            "total_manga",
            "total_novels",
            "total_illust_series",
            "total_novel_series",
        ]
        illust, manga, novel, illust_series, novel_series = tuple(
            map(lambda x: data.pop(x, 0), keys)
        )
        data["art_count"] = UserArtCount(
            illust=illust,
            manga=manga,
            novel=novel,
            illust_series=illust_series,
            novel_series=novel_series,
        )
        return data

    @model_validator(mode="before")
    @classmethod
    def twitter_validate(cls, data: dict) -> dict:
        keys = ["twitter_account", "twitter_url"]
        account, _ = tuple(map(lambda x: data.pop(x, None), keys))
        data["twitter"] = UserTwitter(account=account) if account else None
        return data

    @field_validator("gender", mode="before")
    @classmethod
    def gender_validate(cls, value: str | None) -> UserGender:
        return UserGender.Unknown if not value else UserGender(value)


class UserProfilePublicity(PixivModel):
    gender: bool
    region: bool
    birth_day: bool
    birth_year: bool
    job: bool
    pawoo: bool

    @field_validator("*", mode="before")
    @classmethod
    def field_validate(cls, value: str) -> bool:
        return value == "public"


class UserWorkspace(PixivModel):
    pc: str | None = None
    monitor: str | None = None
    scanner: str | None = None
    mouse: str | None = None
    printer: str | None = None
    desktop: str | None = None
    music: str | None = None
    desk: str | None = None
    chair: str | None = None
    comment: str | None = None
    workspace_image: UrlType | None = None


class FullUser(PixivModel):
    user: User
    profile: UserProfile
    profile_publicity: UserProfilePublicity
    workspace: UserWorkspace

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"<FullUser id={self.user.id} name={self.user.name}>"
