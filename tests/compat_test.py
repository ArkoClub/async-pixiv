import gc
import importlib

import pytest

from async_pixiv.client._client import PixivClient
from async_pixiv.client.api._user import UserPageResult
from async_pixiv.model.user import User, UserBirthday
from async_pixiv.typedefs import UrlType

ACCOUNT_PAYLOAD = {
    "id": 1,
    "name": "demo-user",
    "account": "demo_account",
    "profile_image_urls": {"px_16x16": "https://example.com/avatar.png"},
    "is_premium": False,
    "x_restrict": 0,
    "is_mail_authorized": False,
    "require_policy_agreement": False,
}


def user_payload(user_id: int) -> dict:
    return {
        "id": user_id,
        "name": f"user-{user_id}",
        "account": f"account-{user_id}",
        "profile_image_urls": {"medium": "https://example.com/avatar.png"},
    }


def user_preview_payload(user_id: int) -> dict:
    return {
        "user": user_payload(user_id),
        "illusts": [],
        "novels": [],
        "is_muted": False,
    }


class FakeJSONResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def json(self) -> dict:
        return self.payload

    def raise_error(self):
        return self


def build_bound_user() -> User:
    client = PixivClient()

    async def fake_detail(user_id: int):
        return {"user_id": user_id}

    client.USER.detail = fake_detail
    return User.model_validate(user_payload(1), _pixiv_client=client)


def build_page_result() -> UserPageResult:
    client = PixivClient()

    async def fake_request_get(*_args, **_kwargs):
        return FakeJSONResponse(
            {"user_previews": [user_preview_payload(2)], "next_url": None}
        )

    async def fake_detail(user_id: int):
        return {"user_id": user_id}

    client.request_get = fake_request_get
    client.USER.detail = fake_detail
    return UserPageResult.model_validate(
        {
            "user_previews": [user_preview_payload(1)],
            "next_url": "https://example.com/next",
        },
        _pixiv_client=client,
    )


@pytest.mark.asyncio
async def test_model_validate_keeps_client_binding_after_client_scope_ends():
    user = build_bound_user()
    gc.collect()

    assert await user.detail() == {"user_id": 1}


def test_direct_constructor_binds_client():
    client = PixivClient()
    user = User(
        id=1,
        name="demo-user",
        account="demo_account",
        profile_image_urls={"medium": "https://example.com/avatar.png"},
        _pixiv_client=client,
    )

    assert user._pixiv_client is client


def test_user_model_json_schema_supports_urltype_fields():
    schema = User.model_json_schema()

    assert isinstance(schema, dict)
    assert "properties" in schema


@pytest.mark.asyncio
async def test_page_result_next_keeps_client_after_factory_scope():
    result = build_page_result()
    gc.collect()

    next_result = await result.next()

    assert next_result is not None
    assert next_result.previews[0].id == 2
    assert await next_result.previews[0].user.detail() == {"user_id": 2}


@pytest.mark.asyncio
async def test_login_with_token_returns_bound_account(monkeypatch):
    client = PixivClient()

    async def fake_request_post(*_args, **_kwargs):
        return FakeJSONResponse(
            {
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "user": ACCOUNT_PAYLOAD,
            }
        )

    async def fake_detail(user_id: int):
        return {"user_id": user_id}

    monkeypatch.setattr(client, "request_post", fake_request_post)
    monkeypatch.setattr(client.USER, "detail", fake_detail)

    account = await client.login_with_token("refresh-token")

    assert account._pixiv_client is client
    assert await account.detail() == {"user_id": 1}


def test_urltype_is_plain_url_without_download_helper():
    assert not hasattr(UrlType("https://example.com/file.jpg"), "download")


@pytest.mark.asyncio
async def test_client_download_uses_explicit_url(monkeypatch):
    client = PixivClient()

    async def fake_download(
        url,
        method="GET",
        *,
        output=None,
        chunk_size=None,
        progress_handler=None,
    ):
        return b"image-bytes"

    monkeypatch.setattr(client, "download", fake_download)

    data = await client.download(UrlType("https://example.com/file.jpg"))

    assert data == b"image-bytes"


def test_removed_legacy_modules_are_not_importable():
    for module_name in (
        "async_pixiv.utils.context",
        "async_pixiv.utils.decorator",
        "async_pixiv.utils.singleton",
    ):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(module_name)


def test_user_birthday_date_alias_matches_to_date():
    birthday = UserBirthday(2024, 1, 2)

    assert birthday.date() == birthday.to_date()


@pytest.mark.asyncio
async def test_download_accepts_async_callable_object_progress_handler(monkeypatch):
    client = PixivClient()
    calls = []

    class ProgressHandler:
        async def __call__(self, uploaded, total):
            calls.append((uploaded, total))

    class FakeResponse:
        def __init__(self) -> None:
            self.headers = {"content-length": "4"}

        def raise_for_status(self):
            return self

        async def aiter_bytes(self, _chunk_size):
            yield b"data"

    class FakeStream:
        async def __aenter__(self):
            return FakeResponse()

        async def __aexit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr(client._client, "stream", lambda *args, **kwargs: FakeStream())

    data = await client.download(
        "https://example.com/file.jpg", progress_handler=ProgressHandler()
    )

    assert data == b"data"
    assert calls == [(4, 4)]
